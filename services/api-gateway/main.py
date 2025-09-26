import os, time, json
import asyncpg
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer, KafkaConsumer



app = FastAPI()
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
QUESTION_TOPIC = os.getenv("KAFKA_QUESTION_TOPIC", "questions")
SCORED_TOPIC = os.getenv("KAFKA_SCORED_TOPIC", "scored")

from pydantic import BaseModel

class QuestionRequest(BaseModel):
	question: str
	reference: str = None



# DB
DB_DSN = f"postgresql://{os.getenv('POSTGRES_USER','qauser')}:{os.getenv('POSTGRES_PASSWORD','qapass')}@{os.getenv('POSTGRES_HOST','db')}/{os.getenv('POSTGRES_DB','qa')}"



@app.on_event("startup")
async def startup():
	app.state.pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=5)
	app.state.producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
	app.state.consumer = KafkaConsumer(SCORED_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="api-gateway", auto_offset_reset="earliest", enable_auto_commit=True)



@app.post("/question")
async def post_question(req: QuestionRequest):
	start = time.perf_counter()
	# Generate a unique id for this question (timestamp-based)
	qa_id = int(time.time() * 1000)
	question_payload = {
		"qa_id": qa_id,
		"question": req.question,
		"reference": req.reference
	}
	app.state.producer.send(QUESTION_TOPIC, question_payload)
	app.state.producer.flush()

	# Wait for answer in Kafka
	answer = None
	timeout = 10  # seconds
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
	# Optionally, store in DB if needed
	return {"source": "kafka", **answer, "latency_ms": latency_ms}