from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
cache = {}

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    question = data["question"]

    if question in cache:
        return jsonify({"answer": cache[question], "source": "cache"})

    # Si no está en caché, pedir al score
    r = requests.post("http://score:5000/answer", json={"question": question})
    answer = r.json()["answer"]

    # Guardar en cache
    cache[question] = answer
    return jsonify({"answer": answer, "source": "score"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
