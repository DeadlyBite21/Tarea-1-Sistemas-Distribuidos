import os, json, time
from collections import OrderedDict, deque
from kafka import KafkaConsumer, KafkaProducer

# Configuración
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
QUESTION_TOPIC = os.getenv("KAFKA_QUESTION_TOPIC", "questions")
CACHE_HIT_TOPIC = os.getenv("KAFKA_CACHE_HIT_TOPIC", "cache_hit")
CACHE_MISS_TOPIC = os.getenv("KAFKA_CACHE_MISS_TOPIC", "cache_miss")
ANSWER_TOPIC = os.getenv("KAFKA_ANSWER_TOPIC", "answers")
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "1000"))
CACHE_POLICY = os.getenv("CACHE_POLICY", "LRU")  # LRU, FIFO, LFU
TTL_SECONDS = int(os.getenv("CACHE_TTL", "3600"))

class LRUCache:
    def __init__(self, capacity, ttl):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttl = ttl
    def get(self, key):
        item = self.cache.get(key)
        if item:
            value, ts = item
            if time.time() - ts < self.ttl:
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        return None
    def put(self, key, value):
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class FIFOCache:
    def __init__(self, capacity, ttl):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttl = ttl
    def get(self, key):
        item = self.cache.get(key)
        if item:
            value, ts = item
            if time.time() - ts < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    def put(self, key, value):
        self.cache[key] = (value, time.time())
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

if CACHE_POLICY == "FIFO":
    cache = FIFOCache(CACHE_SIZE, TTL_SECONDS)
else:
    cache = LRUCache(CACHE_SIZE, TTL_SECONDS)

question_consumer = KafkaConsumer(QUESTION_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="cache", auto_offset_reset="earliest", enable_auto_commit=True)
answer_consumer = KafkaConsumer(CACHE_MISS_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="cache-answers", auto_offset_reset="earliest", enable_auto_commit=True)
llm_answer_consumer = KafkaConsumer(ANSWER_TOPIC, bootstrap_servers=KAFKA_BROKER, value_deserializer=lambda m: json.loads(m.decode("utf-8")), group_id="cache-llm", auto_offset_reset="earliest", enable_auto_commit=True)
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))

import threading

def handle_questions():
    print(f"[cache] Escuchando preguntas en Kafka con política {CACHE_POLICY}...")
    for msg in question_consumer:
        data = msg.value
        qa_id = data.get("qa_id")
        question = data.get("question")
        if not qa_id or not question:
            continue
        cache_key = str(qa_id)
        cached = cache.get(cache_key)
        if cached:
            # Cache hit: responde y actualiza almacenamiento
            hit_payload = {"qa_id": qa_id, "answer": cached, "cache": True}
            producer.send(CACHE_HIT_TOPIC, hit_payload)
            print(f"[cache] HIT {qa_id}")
        else:
            # Cache miss: reenvía a responder-llm
            producer.send(CACHE_MISS_TOPIC, data)
            print(f"[cache] MISS {qa_id}")

def handle_llm_answers():
    print(f"[cache] Escuchando respuestas LLM en Kafka...")
    for msg in llm_answer_consumer:
        data = msg.value
        qa_id = data.get("qa_id")
        answer = data.get("answer")
        if qa_id and answer:
            cache_key = str(qa_id)
            cache.put(cache_key, answer)
            print(f"[cache] Guardada respuesta en caché para {qa_id}")

threading.Thread(target=handle_questions, daemon=True).start()
threading.Thread(target=handle_llm_answers, daemon=True).start()

while True:
    time.sleep(1)
