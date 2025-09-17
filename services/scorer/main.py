from fastapi import FastAPI
from pydantic import BaseModel
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer
import numpy as np


app = FastAPI()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


class S(BaseModel):
	reference: str
	candidate: str


@app.post("/score")
def score(s: S):
	# ROUGE-L
	rs = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
	rouge_l = rs.score(s.reference, s.candidate)['rougeL'].fmeasure

	# Coseno
	v = model.encode([s.reference, s.candidate], normalize_embeddings=True)
	cosine = float(np.dot(v[0], v[1]))

	return {"rouge_l": float(rouge_l), "cosine_sim": cosine}