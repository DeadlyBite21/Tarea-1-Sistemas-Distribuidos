import os, time, json
import aioredis, asyncpg
from fastapi import FastAPI, HTTPException
import httpx


app = FastAPI()


# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_TTL = int(os.getenv("REDIS_TTL_SECONDS", "86400"))


# DB
DB_DSN = f"postgresql://{os.getenv('POSTGRES_USER','qauser')}:{os.getenv('POSTGRES_PASSWORD','qapass')}@{os.getenv('POSTGRES_HOST','db')}/{os.getenv('POSTGRES_DB','qa')}"


# Services
RESPONDER_URL = os.getenv("RESPONDER_URL", "http://responder-llm:8001/answer")
SCORER_URL = os.getenv("SCORER_URL", "http://scorer:8002/score")


@app.on_event("startup")
async def startup():
	app.state.redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", encoding="utf-8", decode_responses=True)
	app.state.pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=5)


@app.get("/ask")
async def ask(qa_id: int):
	r = app.state.redis
	cache_key = f"qa:{qa_id}"
	cached = await r.get(cache_key)
	start = time.perf_counter()
	async with app.state.pool.acquire() as conn:
		row = await conn.fetchrow("SELECT id, question_title, question_content, best_answer FROM qa_pairs WHERE id=$1", qa_id)
	if not row:
		raise HTTPException(404, "qa_id no existe")
	if cached:
		data = json.loads(cached)
		latency_ms = int((time.perf_counter()-start)*1000)
		async with app.state.pool.acquire() as conn:
			await conn.execute(
				"INSERT INTO answers(qa_id,llm_provider,llm_answer,rouge_l,cosine_sim,hits,latency_ms) VALUES($1,$2,$3,$4,$5,$6,$7)",
				qa_id, data["provider"], data["answer"], data.get("rouge_l"), data.get("cosine_sim"), data.get("hits",0)+1, latency_ms)
		return {"source":"cache", **data, "latency_ms": latency_ms}

	# Miss: pedir LLM y luego score
	async with httpx.AsyncClient() as client:
		llm_resp = await client.post(RESPONDER_URL, json={"question": row["question_title"] + "\n" + row["question_content"]})
		llm_resp.raise_for_status()
		llm_data = llm_resp.json()
		score_resp = await client.post(SCORER_URL, json={
			"reference": row["best_answer"],
			"candidate": llm_data["answer"]
		})
		score_resp.raise_for_status()
		score = score_resp.json()

	latency_ms = int((time.perf_counter()-start)*1000)

	payload = {
		"provider": llm_data["provider"],
		"answer": llm_data["answer"],
		"rouge_l": score.get("rouge_l"),
		"cosine_sim": score.get("cosine_sim"),
		"hits": 1
	}

	await r.set(cache_key, json.dumps(payload), ex=REDIS_TTL)
	async with app.state.pool.acquire() as conn:
		await conn.execute(
			"INSERT INTO answers(qa_id,llm_provider,llm_answer,rouge_l,cosine_sim,hits,latency_ms) VALUES($1,$2,$3,$4,$5,$6,$7)",
			qa_id, payload["provider"], payload["answer"], payload["rouge_l"], payload["cosine_sim"], payload["hits"], latency_ms)

	return {"source":"llm", **payload, "latency_ms": latency_ms}