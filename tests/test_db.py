from app import db

def fake_result(conf=0.8, sources=("a.md",)):
    return {"answer": "x", "confidence": conf, "sources": list(sources),
            "latency_ms": 10,
            "retrieved": [{"chunk_id": 1, "score": conf},
                          {"chunk_id": 2, "score": conf - 0.1}]}

def test_log_query_stores_chunks(temp_db):
    qid = db.log_query("how to?", fake_result(), 100)
    with db.get_conn() as c:
        n = c.execute("SELECT COUNT(*) FROM retrieved_chunks WHERE query_id=?",
                      (qid,)).fetchone()[0]
    assert qid == 1 and n == 2

def test_feedback_unknown_query_rejected(temp_db):
    assert db.log_feedback(999, 1) is False

def test_stats_counts_refusals(temp_db):
    db.log_query("q1", fake_result(), 100)
    db.log_query("q2", fake_result(sources=()), 100)  # no sources = refused
    s = db.get_stats()
    assert s["total_queries"] == 2 and s["refused"] == 1