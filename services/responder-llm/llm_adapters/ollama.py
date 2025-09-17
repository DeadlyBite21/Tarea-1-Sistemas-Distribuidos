# services/responder-llm/llm_adapters/ollama.py
from __future__ import annotations
import httpx

# API reference (mínimo): POST {OLLAMA_HOST}/api/generate
# Body:
# {"model": "<nombre-modelo>", "prompt": "<prompt>", "stream": false}

class OllamaError(RuntimeError):
    pass

async def generate(
    prompt: str,
    host: str = "http://ollama:11434",
    model: str = "llama3.1",
    timeout_s: float = 120.0,
    options: dict | None = None,  # p.ej., {"temperature": 0.7}
) -> str:
    url = f"{host.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    if options:
        payload["options"] = options

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        r = await client.post(url, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise OllamaError(f"HTTP {r.status_code} al llamar Ollama: {r.text}") from e

        data = r.json()
        # Respuesta típica: {"model": "...", "created_at": "...", "response": "texto...", ...}
        text = data.get("response")
        if not isinstance(text, str):
            raise OllamaError(f"Respuesta inesperada de Ollama: {data}")
        return text
