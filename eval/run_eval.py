import json
from app.retrieval import retrieve

qs = json.load(open("eval/questions.json"))
answerable = [x for x in qs if x["files"]]
unanswerable = [x for x in qs if not x["files"]]

for size in (100, 200):
    hits = {1: 0, 3: 0, 5: 0}
    for x in answerable:
        res = retrieve(x["q"], k=5, size=size)
        for k in hits:
            if any(r["source"] in x["files"] for r in res[:k]):
                hits[k] += 1
    n = len(answerable)
    print(f"size={size}  " + "  ".join(f"recall@{k}={hits[k]/n:.2f}" for k in hits))
    ans_top = sorted(retrieve(x["q"], k=1, size=size)[0]["score"] for x in answerable)
    off_top = sorted(retrieve(x["q"], k=1, size=size)[0]["score"] for x in unanswerable)
    print("  top score, answerable:  ", [round(s, 2) for s in ans_top])
    print("  top score, unanswerable:", [round(s, 2) for s in off_top])