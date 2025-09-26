
import os, json
from kafka import KafkaConsumer, KafkaProducer
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
import numpy as np

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
ANSWER_TOPIC = os.getenv("KAFKA_ANSWER_TOPIC", "answers")
SCORED_TOPIC = os.getenv("KAFKA_SCORED_TOPIC", "scored")

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def run_kafka_scorer():
	consumer = KafkaConsumer(ANSWER_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="scorer", auto_offset_reset="earliest", enable_auto_commit=True)
	producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
	print("[scorer] Esperando respuestas de LLM en Kafka...")
	for msg in consumer:
		data = msg.value
		qa_id = data.get("qa_id")
		candidate = data.get("answer")
		reference = data.get("reference")
		provider = data.get("provider")
		if not qa_id or not candidate or not reference:
			continue
		# Calcular score
		rs = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
		rouge_l = rs.score(reference, candidate)['rougeL'].fmeasure
		v = model.encode([reference, candidate], normalize_embeddings=True)
		cosine = float(np.dot(v[0], v[1]))
		scored_payload = {
			"qa_id": qa_id,
			"provider": provider,
			"answer": candidate,
			"rouge_l": float(rouge_l),
			"cosine_sim": cosine
		}
		producer.send(SCORED_TOPIC, scored_payload)
		producer.flush()
		print(f"[scorer] Score enviado para pregunta {qa_id}")

if __name__ == "__main__":
	run_kafka_scorer()