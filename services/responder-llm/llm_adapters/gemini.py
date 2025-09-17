# services/responder-llm/llm_adapters/gemini.py
from __future__ import annotations
import httpx

# API reference (mínimo): POST
# https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=API_KEY
# Body:
# {"contents":[{"parts":[{"text": "<prompt>"}]}]}

class GeminiError(RuntimeError):
    pass

def _extract_text(data: dict) -> str:
    # Trata de extraer el texto de la primera candidata
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise GeminiError(f"No se pudo extraer texto de la respuesta: {e}. Respuesta: {data}") from e

async def generate(
    prompt: str,
    api_key: str,
    model: str = "gemini-1.5-flash",
    temperature: float = 0.7,
    timeout_s: float = 60.0,
) -> str:
    if not api_key:
        raise GeminiError("Falta GEMINI_API_KEY")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        r = await client.post(url, params={"key": api_key}, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = r.text
            raise GeminiError(f"HTTP {r.status_code} al llamar Gemini: {detail}") from e

        data = r.json()
        return _extract_text(data)
