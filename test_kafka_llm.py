import json
import uuid
import time
from kafka import KafkaProducer, KafkaConsumer

KAFKA_BROKER = "localhost:9092"
QUESTION_TOPIC = "questions"
ANSWER_TOPIC = "answers"

def send_question(producer, qa_id, question):
    payload = {
        "qa_id": qa_id,
        "question": question,
        "reference": "test-script"
    }
    producer.send(QUESTION_TOPIC, value=payload)
    producer.flush()
    print(f"[test] Pregunta enviada: {payload}")

def listen_for_answer(consumer, qa_id, timeout=20):
    print(f"[test] Esperando respuesta para qa_id={qa_id}...")
    start = time.time()
    for msg in consumer:
        data = msg.value
        if data.get("qa_id") == qa_id:
            print(f"[test] Respuesta recibida: {data}")
            return data
        if time.time() - start > timeout:
            print("[test] Timeout esperando respuesta.")
            return None

def main():
    qa_id = str(uuid.uuid4())
    question = "¿Cuál es la capital de Francia?"
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    consumer = KafkaConsumer(ANSWER_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="test-llm", auto_offset_reset="earliest", enable_auto_commit=True)
    send_question(producer, qa_id, question)
    listen_for_answer(consumer, qa_id)

if __name__ == "__main__":
    main()
