from flask import Flask
import requests

app = Flask(__name__)

@app.route("/")
def generate_query():
    # Pedir una pregunta random al storage
    r = requests.get("http://storage:5000/random")
    data = r.json()

    if "error" in data:
        return "No hay preguntas en storage"

    q = data["question"]

    # Mandar al cache
    r2 = requests.post("http://cache:5000/query", json={"question": q})

    return f"Consulta enviada: {q} -> {r2.text}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
