from flask import Flask, request, jsonify
import sqlite3, csv, os

app = Flask(__name__)
DB = "data.db"
DATASET = "train.csv"   # asegúrate que esté en la carpeta storage/

# ---------- Inicializar DB ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS qa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        best_answer TEXT,
        generated_answer TEXT,
        score REAL,
        count INTEGER DEFAULT 1
    )""")
    conn.commit()
    conn.close()

# ---------- Cargar dataset si DB está vacía ----------
def load_dataset():
    if not os.path.exists(DATASET):
        print(f"⚠️ Dataset {DATASET} no encontrado en el contenedor")
        return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with open(DATASET, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # saltar header
        for row in reader:
            # dataset: [class, title, content, best_answer]
            try:
                _, title, content, best = row
            except ValueError:
                continue
            q = title if title else content
            c.execute("INSERT INTO qa (question, best_answer) VALUES (?,?)", (q, best))
    conn.commit()
    conn.close()

# ---------- Endpoint para guardar respuesta ----------
@app.route("/save", methods=["POST"])
def save():
    data = request.get_json()
    q = data["q"]
    gen_a = data["a"]
    score = data.get("score", None)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    row = c.execute("SELECT id, count FROM qa WHERE question=? LIMIT 1", (q,)).fetchone()
    if row:
        c.execute("UPDATE qa SET generated_answer=?, score=?, count=? WHERE id=?",
                  (gen_a, score, row[1]+1, row[0]))
    else:
        c.execute("INSERT INTO qa (question, generated_answer, score) VALUES (?,?,?)",
                  (q, gen_a, score))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

# ---------- Endpoint para listar registros ----------
@app.route("/all", methods=["GET"])
def get_all():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM qa LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# ---------- Endpoint para obtener una pregunta random ----------
@app.route("/random", methods=["GET"])
def get_random():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, question, best_answer FROM qa ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"id": row[0], "question": row[1], "best_answer": row[2]})
    else:
        return jsonify({"error": "No data in DB"})

# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM qa")
    if c.fetchone()[0] == 0:
        print("📥 Cargando dataset en la base de datos...")
        load_dataset()
    conn.close()

    print("✅ Storage iniciado en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
