
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuración global de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

@app.route("/answer", methods=["POST"])
def generate_answer():
    data = request.get_json()
    question = data["question"]

    # Construir payload para la API REST
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    # Llamar a la API REST de Gemini
    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        # Extraer respuesta del modelo
        answer = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Guardar en storage
    try:
        requests.post("http://storage:5000/save", json={"q": question, "a": answer})
    except Exception:
        pass  # Ignorar errores de almacenamiento para no romper la respuesta principal

    return jsonify({"answer": answer})

# Endpoint para ver el modelo configurado
@app.route("/model", methods=["GET"])
def get_model():
    return jsonify({"model": GEMINI_MODEL})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
