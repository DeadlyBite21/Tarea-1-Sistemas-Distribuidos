
import os
import csv
import sys
import time
import logging
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = "qa"
POSTGRES_USER = os.environ.get("POSTGRES_USER", "qauser")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "qapass")

CSV_PATH = os.environ.get("CSV_PATH", "qa-plataform/Data/yahoo_answers.csv")
BATCH_SIZE = int(os.environ.get("INGEST_BATCH_SIZE", 1000))
ENCODING = os.environ.get("CSV_ENCODING", "utf-8")

def detect_columns(header):
    h = [c.lower() for c in header]
    q_keys = ["question", "q", "title", "query", "subject"]
    a_keys = ["answer", "best_answer", "bestanswer", "accepted_answer", "reply", "content"]
    question_col = None
    answer_col = None
    for k in q_keys:
        for i, col in enumerate(h):
            if k in col:
                question_col = header[i]
                break
        if question_col:
            break
    for k in a_keys:
        for i, col in enumerate(h):
            if k in col:
                answer_col = header[i]
                break
        if answer_col:
            break
    if not question_col or not answer_col:
        # fallback: first two columns
        question_col = header[0]
        answer_col = header[1] if len(header) > 1 else None
    return question_col, answer_col

def create_database_if_not_exists():
    # Connect to default database to create target database
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname="postgres",
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {POSTGRES_DB}")
            logging.info(f"Database '{POSTGRES_DB}' created.")
    conn.close()

def create_table_if_not_exists(conn):
    create_sql = """
    CREATE TABLE IF NOT EXISTS qa_pairs (
        id SERIAL PRIMARY KEY,
        question_title TEXT,
        question_content TEXT,
        best_answer TEXT,
        metadata JSONB,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_sql)
    conn.commit()

def main():
    if not os.path.exists(CSV_PATH):
        logging.error("CSV not found at %s", CSV_PATH)
        sys.exit(1)

    create_database_if_not_exists()

    # Connect to target DB
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    create_table_if_not_exists(conn)

    inserted = 0
    start = time.time()

    # Read CSV and insert in batches (sin encabezado)
    with open(CSV_PATH, "r", encoding=ENCODING, errors="replace", newline="") as f:
        reader = csv.reader(f)
        batch = []
        with conn.cursor() as cur:
            insert_sql = "INSERT INTO qa_pairs (question_title, question_content, best_answer, metadata) VALUES %s"
            for row in reader:
                if len(row) < 3:
                    continue
                qt = row[0].strip()
                qc = row[1].strip()
                ba = row[2].strip()
                # Forzar metadata a None para evitar errores de formato JSON
                meta = None
                batch.append((qt, qc, ba, meta))
                if len(batch) >= BATCH_SIZE:
                    psycopg2.extras.execute_values(cur, insert_sql, batch, template=None, page_size=1000)
                    conn.commit()
                    inserted += len(batch)
                    logging.info("Inserted %d rows so far...", inserted)
                    batch = []
            # final batch
            if batch:
                psycopg2.extras.execute_values(cur, insert_sql, batch, template=None, page_size=1000)
                conn.commit()
                inserted += len(batch)
    elapsed = time.time() - start
    logging.info("Ingest finished. Total rows inserted: %d (%.2f rows/s)", inserted, (inserted / elapsed) if elapsed>0 else 0.0)
    conn.close()

if __name__ == "__main__":
    main()
