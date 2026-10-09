import json, functools
import faiss
from app.embed import embed

DEFAULT_SIZE = 200
THRESHOLD = 0.45  # 0.35 before evalutions

@functools.lru_cache(maxsize=None)
def load(size):
    index = faiss.read_index(f"data/index_{size}.faiss")
    with open(f"data/chunks_{size}.json", encoding="utf-8") as f:
        chunks = json.load(f)
    assert index.ntotal == len(chunks), "index and chunks out of sync"
    return index, chunks

def retrieve(question, k=5, size=DEFAULT_SIZE):
    index, chunks = load(size)
    scores, ids = index.search(embed([question]), k)
    return [{**chunks[i], "score": float(s)}
            for s, i in zip(scores[0], ids[0]) if i != -1]

def is_confident(results, threshold=THRESHOLD):
    return bool(results) and results[0]["score"] >= threshold

if __name__ == "__main__":
    import sys
    res = retrieve(" ".join(sys.argv[1:]))
    for r in res:
        print(f"{r['score']:.3f}  {r['source']} | {r['heading'][:50]}")
    print("confident:", is_confident(res))