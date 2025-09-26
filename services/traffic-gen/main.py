import os, time, random, asyncio, json, sys
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
QUESTION_TOPIC = os.getenv('KAFKA_QUESTION_TOPIC', 'questions')
RATE = float(os.getenv('TRAFFIC_RATE', '6')) # eventos/min
DISTR = os.getenv('TRAFFIC_DISTR', 'poisson') # poisson|lognormal|pareto
MU = float(os.getenv('LOGNORMAL_MU','0.0'))
SIGMA = float(os.getenv('LOGNORMAL_SIGMA','1.0'))
ALPHA = float(os.getenv('PARETO_SHAPE','1.5'))

Q_MIN, Q_MAX = 1, 12000

def interarrival_seconds():
    if DISTR == 'poisson':
        lam = RATE / 60.0
        return random.expovariate(lam) if lam > 0 else 1.0
    if DISTR == 'lognormal':
        return random.lognormvariate(MU, SIGMA)
    if DISTR == 'pareto':
        return random.paretovariate(ALPHA)
    return 1.0

def make_producer():
    try:
        p = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        print(f"[traffic-gen] Connected to Kafka at {KAFKA_BROKER}")
        return p
    except NoBrokersAvailable as e:
        print(f"[traffic-gen][ERROR] No brokers available at {KAFKA_BROKER}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[traffic-gen][ERROR] Producer creation failed: {e}", file=sys.stderr)
        return None

async def main():
    print(f"[traffic-gen] Starting. topic={QUESTION_TOPIC} rate={RATE} distrib={DISTR}")
    producer = make_producer()
    # try reconnect loop
    while producer is None:
        print("[traffic-gen] Esperando a Kafka... reintentando en 5s")
        await asyncio.sleep(5)
        producer = make_producer()

    while True:
        qa_id = random.randint(Q_MIN, Q_MAX)
        payload = {
            "qa_id": qa_id,
            "question": f"Pregunta simulada {qa_id}",
            "reference": f"Respuesta simulada {qa_id}"
        }
        try:
            future = producer.send(QUESTION_TOPIC, payload)
            # confirmar envío
            result = future.get(timeout=10)
            print(f"[traffic-gen] Pregunta enviada: {qa_id}")
        except KafkaError as ke:
            print(f"[traffic-gen][KAFKA ERROR] {ke}", file=sys.stderr)
            # intentar recrear producer
            producer = None
            while producer is None:
                await asyncio.sleep(5)
                producer = make_producer()
        except Exception as ex:
            print(f"[traffic-gen][ERROR] send failed: {ex}", file=sys.stderr)

        delay = interarrival_seconds()
        # evita delays absurdos
        if delay is None or delay <= 0:
            delay = 1.0
        await asyncio.sleep(delay)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[traffic-gen][FATAL] {e}", file=sys.stderr)
        raise
