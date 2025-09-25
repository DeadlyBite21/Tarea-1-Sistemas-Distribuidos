
CREATE TABLE IF NOT EXISTS qa_pairs (
  id SERIAL PRIMARY KEY,
  question_title TEXT,
  question_content TEXT,
  best_answer TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_qa_pairs_question_tsv ON qa_pairs USING gin (to_tsvector('english', question_title));
