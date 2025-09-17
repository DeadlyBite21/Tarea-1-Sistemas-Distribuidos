import os
from fastapi import FastAPI
from pydantic import BaseModel
import httpx


class Q(BaseModel):
	question: str


app = FastAPI()
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


@app.post("/answer")
async def answer(q: Q):
	if PROVIDER == "gemini":
		text = await call_gemini(q.question)
	elif PROVIDER == "ollama":
		text = await call_ollama(q.question)
	else:
		text = f"(mock) Respuesta plausible a: {q.question[:120]}..."
	return {"provider": PROVIDER, "answer": text}