import re, time
from app import llm
from app.embed import clean_heading
from app.retrieval import retrieve, is_confident

SYSTEM = (
    "You answer questions about the FastAPI documentation. "
    "Use ONLY the numbered excerpts provided. Cite the excerpts you used "
    "inline like [1] or [2][3]. If the excerpts do not contain the answer, "
    "reply exactly: I don't know. Do not use outside knowledge. "
    "Do not write code unless that exact code appears in the excerpts; "
    "otherwise describe it in words. Be concise: at most 120 words."
)
REFUSAL = "I don't know based on the FastAPI docs."

def build_prompt(question, chunks):
    ctx = "\n\n".join(
        f"[{i}] ({c['source']} - {clean_heading(c['heading'])})\n{c['text']}"
        for i, c in enumerate(chunks, 1))
    return f"Excerpts:\n{ctx}\n\nQuestion: {question}"

def cited_sources(answer, chunks):
    nums = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer)})
    picked = [chunks[n - 1] for n in nums if 1 <= n <= len(chunks)]
    return picked or chunks[:1]  # fallback if the LLM cited nothing valid

def ask(question, k=5):
    t0 = time.perf_counter()
    results = retrieve(question, k)
    confidence = results[0]["score"] if results else 0.0
    if not is_confident(results):
        answer, sources = REFUSAL, []
    else:
        answer = llm.generate_answer(SYSTEM, build_prompt(question, results))
        norm = answer.lower().replace("’", "'")
        sources = [] if norm.startswith("i don't know") else cited_sources(answer, results)
    return {
        "answer": answer,
        "confidence": round(confidence, 3),
        "sources": [{"chunk_id": c["id"], "source": c["source"],
                     "heading": clean_heading(c["heading"]),
                     "score": round(c["score"], 3)} for c in sources],
        "retrieved": [{"chunk_id": r["id"], "score": round(r["score"], 3)} for r in results],
        "latency_ms": round((time.perf_counter() - t0) * 1000),
    }