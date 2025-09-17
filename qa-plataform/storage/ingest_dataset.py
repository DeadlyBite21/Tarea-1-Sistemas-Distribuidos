#!/usr/bin/env python3
# storage/ingest_dataset.py
import os
import csv
import sys
import time
import logging
from psycopg2 import connect, sql
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_DB = os.environ.get("POSTGRES_DB", "qa")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "qauser")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "qa_pass")

CSV_PATH = os.environ.get("CSV_PATH", "/data/yahoo_answers.csv")
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

def create_table_if_not_exists(conn):
    create_sql = """
    CREATE TABLE IF NOT EXISTS qa_pairs (
      id SERIAL PRIMARY KEY,
      question TEXT,
      answer TEXT,
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

    # Connect
    conn = connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    create_table_if_not_exists(conn)

    inserted = 0
    start = time.time()

    # Read CSV and insert in batches
    with open(CSV_PATH, "r", encoding=ENCODING, errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        if not header:
            logging.error("CSV has no header")
            sys.exit(1)
        q_col, a_col = detect_columns(header)
        if not a_col:
            logging.error("No answer column detected and CSV has less than 2 columns. Check CSV.")
            sys.exit(1)
        logging.info("Detected columns -> question: %s ; answer: %s", q_col, a_col)

        batch = []
        with conn.cursor() as cur:
            insert_sql = "INSERT INTO qa_pairs (question, answer, metadata) VALUES %s"
            for row in reader:
                q = row.get(q_col, "").strip()
                a = row.get(a_col, "").strip()
                if not q and not a:
                    continue
                batch.append((q, a, None))
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
