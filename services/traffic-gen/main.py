import os, time, random, math, asyncio
import httpx


API_URL = os.getenv('API_URL', 'http://localhost:8000/ask')
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
	async with httpx.AsyncClient(timeout=30) as client:
		while True:
			qa_id = random.randint(Q_MIN, Q_MAX)
			try:
				r = await client.get(API_URL, params={"qa_id": qa_id})
				r.raise_for_status()
			except Exception as e:
				print("error", e)
			delay = await interarrival_seconds()
			await asyncio.sleep(delay)


if __name__ == "__main__":
	asyncio.run(main())