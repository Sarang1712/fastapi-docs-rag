from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.rag import ask
from app.db import init_db, log_query, log_feedback, get_stats
from app.retrieval import DEFAULT_SIZE

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="FastAPI Docs RAG Assistant", lifespan=lifespan)

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class FeedbackRequest(BaseModel):
    query_id: int
    rating: Literal[-1, 1]

@app.post("/ask")
def ask_endpoint(req: AskRequest):
    result = ask(req.question)
    result["query_id"] = log_query(req.question, result, DEFAULT_SIZE)
    return result

@app.post("/feedback")
def feedback_endpoint(req: FeedbackRequest):
    if not log_feedback(req.query_id, req.rating):
        raise HTTPException(status_code=404, detail="query_id not found")
    return {"status": "ok"}

@app.get("/stats")
def stats_endpoint():
    return get_stats()