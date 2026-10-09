import json
from app.retrieval import retrieve

qs = json.load(open("eval/questions.json"))
for x in qs:
    if not x["files"]:
        continue
    res = retrieve(x["q"], k=5, size=200)
    rank = next((i for i, r in enumerate(res, 1) if r["source"] in x["files"]), None)
    if rank == 1:
        print(f"OK   rank 1 | {x['q']}")
        continue
    print(f"\nCHECK rank={rank} | {x['q']}\n  expected: {x['files']}")
    for i, r in enumerate(res[:4], 1):
        print(f"  {i}. {r['score']:.2f} {r['source']} | {r['heading'][:50]}")