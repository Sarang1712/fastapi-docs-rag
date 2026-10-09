import os, sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence REAL NOT NULL,
    refused INTEGER NOT NULL CHECK (refused IN (0, 1)),
    latency_ms INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS retrieved_chunks (
    query_id INTEGER NOT NULL REFERENCES queries(id),
    rank INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    score REAL NOT NULL,
    PRIMARY KEY (query_id, rank)
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER NOT NULL REFERENCES queries(id),
    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

def db_path():
    return os.environ.get("RAG_DB", "data/app.db")

@contextmanager
def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

def log_query(question, result, chunk_size):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO queries (question, answer, confidence, refused, latency_ms, chunk_size) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (question, result["answer"], result["confidence"],
             int(not result["sources"]), result["latency_ms"], chunk_size))
        qid = cur.lastrowid
        conn.executemany(
            "INSERT INTO retrieved_chunks (query_id, rank, chunk_id, score) VALUES (?, ?, ?, ?)",
            [(qid, i, c["chunk_id"], c["score"])
             for i, c in enumerate(result["retrieved"], 1)])
        return qid

LOW_CONF = 0.55  # p0.45 before eval

def log_feedback(query_id, rating):
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO feedback (query_id, rating) VALUES (?, ?)",
                         (query_id, rating))
        return True
    except sqlite3.IntegrityError:  # foreign key: no such query
        return False

def get_stats(low_conf=LOW_CONF):
    with get_conn() as conn:
        summary = dict(conn.execute(
            "SELECT COUNT(*) AS total_queries, "
            "COALESCE(SUM(refused), 0) AS refused, "
            "ROUND(AVG(confidence), 3) AS avg_confidence, "
            "ROUND(AVG(latency_ms)) AS avg_latency_ms FROM queries").fetchone())
        feedback = [dict(r) for r in conn.execute(
            "SELECT rating, COUNT(*) AS count FROM feedback GROUP BY rating")]
        low = [dict(r) for r in conn.execute(
            "SELECT id, question, confidence FROM queries "
            "WHERE refused = 0 AND confidence < ? ORDER BY confidence LIMIT 5",
            (low_conf,))]
    return {**summary, "feedback_counts": feedback, "low_confidence_answers": low}