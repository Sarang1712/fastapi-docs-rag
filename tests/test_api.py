from fastapi.testclient import TestClient
from app import llm
from app.main import app

def test_ask_feedback_stats_flow(temp_db, monkeypatch):
    monkeypatch.setattr(llm, "generate_answer", lambda system, user: "Use Query().")
    with TestClient(app) as client:
        r = client.post("/ask", json={"question": "How do I declare a query parameter?"})
        assert r.status_code == 200
        qid = r.json()["query_id"]

        assert client.post("/feedback", json={"query_id": qid, "rating": 1}).status_code == 200
        assert client.post("/feedback", json={"query_id": 9999, "rating": 1}).status_code == 404
        assert client.post("/feedback", json={"query_id": qid, "rating": 5}).status_code == 422

        s = client.get("/stats").json()
        assert s["total_queries"] == 1

def test_unrelated_question_refused_without_calling_llm(temp_db, monkeypatch):
    def boom(system, user):
        raise AssertionError("LLM must not be called on refusal")
    monkeypatch.setattr(llm, "generate_answer", boom)
    with TestClient(app) as client:
        r = client.post("/ask", json={"question": "What is the capital of France?"})
        assert r.status_code == 200
        assert r.json()["sources"] == []