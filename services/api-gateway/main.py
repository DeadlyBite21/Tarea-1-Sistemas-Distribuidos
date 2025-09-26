import os, time, json
import asyncpg
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer



app = FastAPI()
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
QUESTION_TOPIC = os.getenv("KAFKA_QUESTION_TOPIC", "questions")
SCORED_TOPIC = os.getenv("KAFKA_SCORED_TOPIC", "scored")



# DB
DB_DSN = f"postgresql://{os.getenv('POSTGRES_USER','qauser')}:{os.getenv('POSTGRES_PASSWORD','qapass')}@{os.getenv('POSTGRES_HOST','db')}/{os.getenv('POSTGRES_DB','qa')}"



@app.on_event("startup")
async def startup():
	app.state.pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=5)
	app.state.producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
	app.state.consumer = KafkaConsumer(SCORED_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="api-gateway", auto_offset_reset="earliest", enable_auto_commit=True)



@app.get("/ask")
async def ask(qa_id: int):
	start = time.perf_counter()
	async with app.state.pool.acquire() as conn:
		row = await conn.fetchrow("SELECT id, question_title, question_content, best_answer FROM qa_pairs WHERE id=$1", qa_id)
	if not row:
		raise HTTPException(404, "qa_id no existe")

	# Enviar pregunta a Kafka
	question_payload = {
		"qa_id": qa_id,
		"question": row["question_title"] + "\n" + row["question_content"],
		"reference": row["best_answer"]
	}
	app.state.producer.send(QUESTION_TOPIC, question_payload)
	app.state.producer.flush()

	# Esperar respuesta en Kafka
	answer = None
	timeout = 10  # segundos
	t0 = time.time()
	for msg in app.state.consumer:
		data = msg.value
		if data.get("qa_id") == qa_id:
			answer = data
			break
		if time.time() - t0 > timeout:
			break

	if not answer:
		raise HTTPException(504, "No se recibió respuesta de LLM/Scorer por Kafka")

	latency_ms = int((time.perf_counter()-start)*1000)
	async with app.state.pool.acquire() as conn:
		await conn.execute(
			"INSERT INTO answers(qa_id,llm_provider,llm_answer,rouge_l,cosine_sim,hits,latency_ms) VALUES($1,$2,$3,$4,$5,$6,$7)",
			qa_id, answer.get("provider"), answer.get("answer"), answer.get("rouge_l"), answer.get("cosine_sim"), 1, latency_ms)

	return {"source":"kafka", **answer, "latency_ms": latency_ms}