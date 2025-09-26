import os, time, random, math, asyncio, json
from kafka import KafkaProducer


KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
QUESTION_TOPIC = os.getenv('KAFKA_QUESTION_TOPIC', 'questions')
RATE = float(os.getenv('TRAFFIC_RATE', '6')) # eventos/min
DISTR = os.getenv('TRAFFIC_DISTR', 'poisson') # poisson|lognormal|pareto
MU = float(os.getenv('LOGNORMAL_MU','0.0'))
SIGMA = float(os.getenv('LOGNORMAL_SIGMA','1.0'))
ALPHA = float(os.getenv('PARETO_SHAPE','1.5'))


# id de preguntas a muestrear (suponiendo 1..N)
Q_MIN, Q_MAX = 1, 12000


async def interarrival_seconds():
	if DISTR == 'poisson':
		lam = RATE / 60.0 # por segundo
		return random.expovariate(lam)
	if DISTR == 'lognormal':
		return random.lognormvariate(MU, SIGMA)
	if DISTR == 'pareto':
		return (random.paretovariate(ALPHA))
	return 1.0


async def main():
	producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
	while True:
		qa_id = random.randint(Q_MIN, Q_MAX)
		question_payload = {
			"qa_id": qa_id,
			"question": f"Pregunta simulada {qa_id}",
			"reference": f"Respuesta simulada {qa_id}"
		}
		producer.send(QUESTION_TOPIC, question_payload)
		producer.flush()
		print(f"[traffic-gen] Pregunta enviada: {qa_id}")
		delay = await interarrival_seconds()
		await asyncio.sleep(delay)


if __name__ == "__main__":
	asyncio.run(main())