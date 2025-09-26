import os, json, time
from kafka import KafkaConsumer, KafkaProducer
import httpx





KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
QUESTION_TOPIC = os.getenv("KAFKA_QUESTION_TOPIC", "questions")
ANSWER_TOPIC = os.getenv("KAFKA_ANSWER_TOPIC", "answers")
PROVIDER = os.getenv("LLM_PROVIDER", "mock")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")


async def call_gemini(prompt: str) -> str:
	# Minimal: usa REST de Generative Language API
	url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
	async with httpx.AsyncClient(timeout=60) as client:
		r = await client.post(url, params={"key": GEMINI_KEY}, json={"contents":[{"parts":[{"text": prompt}]}]})
		r.raise_for_status()
		data = r.json()
		return data["candidates"][0]["content"]["parts"][0]["text"]


async def call_ollama(prompt: str) -> str:
	async with httpx.AsyncClient(timeout=120) as client:
		r = await client.post(f"{OLLAMA_HOST}/api/generate", json={"model":"llama3.1", "prompt": prompt})
		r.raise_for_status()
		# stream simplificado
		return r.text



def run_kafka_llm():
	consumer = KafkaConsumer(QUESTION_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="responder-llm", auto_offset_reset="earliest", enable_auto_commit=True)
	producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
	print("[responder-llm] Esperando preguntas en Kafka...")
	import asyncio
	async def process_message(data):
		qa_id = data.get("qa_id")
		question = data.get("question")
		reference = data.get("reference")
		if not qa_id or not question:
			return
		# Llama al modelo
		if PROVIDER == "gemini":
			text = await call_gemini(question)
		elif PROVIDER == "ollama":
			text = await call_ollama(question)
		else:
			text = f"(mock) Respuesta plausible a: {question[:120]}..."
		# Produce respuesta en Kafka
		answer_payload = {
			"qa_id": qa_id,
			"provider": PROVIDER,
			"answer": text,
			"reference": reference
		}
		producer.send(ANSWER_TOPIC, answer_payload)
		producer.flush()
		print(f"[responder-llm] Respondió pregunta {qa_id}")

	loop = asyncio.get_event_loop()
	for msg in consumer:
		data = msg.value
		loop.run_until_complete(process_message(data))

if __name__ == "__main__":
	run_kafka_llm()