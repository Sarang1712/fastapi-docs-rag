# FastAPI Docs RAG Assistant

A question-answering API over the official FastAPI documentation. It answers only from the retrieved docs, attaches citations (file + heading) from chunk metadata, and says "I don't know" when the docs don't cover the question. Every request is logged to SQLite, and retrieval quality is measured on a hand-checked question set.

## Problem

LLMs write fluent answers even when they don't know the answer. For documentation Q&A, a wrong but confident answer is worse than no answer. This project tackles that with retrieval-augmented generation (RAG), a code-level refusal rule, and measurement of how well retrieval actually works.

## Approach

```
Question -> POST /ask
  -> embed question (all-MiniLM-L6-v2, normalized)
  -> FAISS exact search (IndexFlatIP = cosine similarity), top-5 chunks
  -> top score < 0.45 ?  yes -> "I don't know" (LLM is never called)
                         no  -> grounded prompt -> LLM (gpt-oss-20b via Groq) -> answer
  -> citations (source file + heading) attached by code from chunk metadata
  -> request logged to SQLite (question, chunk ids, scores, answer, latency, confidence)
```

Design decisions:
- **Refusal is decided in code, before the LLM.** Vector search always returns nearest chunks, even for off-topic questions, so a tuned similarity threshold gates the LLM.
- **Citations come from metadata, not the LLM,** so they cannot be invented.
- **The LLM sits behind one function (`generate_answer`)** so the provider can be swapped and tests can mock it.
- **Heading-first chunking** (split on `#`-`####`, ignoring `#` in code fences), then word windows with 20-word overlap, compared at 100 and 200 words.
- **Exact search (`IndexFlatIP`)** is fast enough for about 2,000 chunks. Approximate indexes only matter at much larger scale.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /ask` | Answer a question. Returns answer, sources, confidence, and `query_id`. |
| `POST /feedback` | Thumbs up/down (`rating` = 1 or -1) for a `query_id`. Unknown id returns 404. |
| `GET /stats` | SQL aggregates: total queries, refusals, average latency, feedback counts, low-confidence answers. |

Interactive docs: `http://127.0.0.1:8000/docs`

## Database (SQLite)

- `queries`: one row per question (answer, confidence, refused, latency, chunk size)
- `retrieved_chunks`: one row per retrieved chunk, keyed by `(query_id, rank)`
- `feedback`: ratings linked to a query

Foreign keys are enabled per connection, writes run in transactions (commit or rollback), and `/stats` uses SQL (`COUNT`, `AVG`, `SUM`, `GROUP BY`) rather than Python-side counting.

## Evaluation

Retrieval is evaluated **without calling the LLM**, so a retrieval failure can be told apart from a generation failure.

- 20 questions: 16 answerable (each mapped to the doc file containing the answer) and 4 unanswerable (to test refusal).
- Ground-truth files were checked against the docs after the first run; no labels needed changing.
- Metric: **recall@k** = fraction of answerable questions where the correct file appears among the top k chunks.

| Chunk size | recall@1 | recall@3 | recall@5 |
|---|---|---|---|
| **200 words (default)** | 0.62 (10/16) | 0.75 (12/16) | 0.94 (15/16) |
| 100 words | 0.56 (9/16) | 0.81 (13/16) | 0.88 (14/16) |

**Reading the table:** the two sizes differ by one question at each k, and neither wins consistently. With 16 questions this is within noise, so no chunk size is declared better.

### Refusal threshold

Top-1 similarity scores on the eval set:
- Answerable questions: minimum **0.49**
- Unanswerable questions: maximum **0.40**

The threshold is set to **0.45**, in the gap between the two groups. Only 4 unanswerable questions were used, so this is evidence, not proof. The tradeoff: a higher threshold refuses vague but valid questions, a lower one lets off-topic questions reach the LLM. Here, refusing is preferred over answering off-topic.

### What the misses showed

- **Ambiguous words fool embeddings:** "run code at startup" retrieved server-boot pages instead of lifespan events; "path parameter" retrieved URL-path pages.
- **High similarity is not correctness:** for "How do I enable CORS?", a middleware page that only links to the CORS page scored higher (0.69) than the CORS page itself (0.61). A threshold filters off-topic queries; it cannot rank relevant pages.
- **Vague questions score low:** "How do I test my app?" topped out at 0.49, barely above the threshold.

## Tests

`pytest` suite: database layer (temp database), API endpoints (temp database, mocked LLM, including a check that the LLM is not called on refusal), and chunking/threshold functions. Mocked tests verify the code's plumbing, not the quality of the model's answers; quality is measured by the evaluation above.

```
pip install -r requirements-dev.txt
pytest -q
```

## Run locally

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
# put GROQ_API_KEY in .env (never commit it)
python -m app.ingest      # download the FastAPI docs
python -m app.embed       # build chunks + FAISS indexes (sizes 100 and 200)
uvicorn app.main:app --reload
python -m eval.run_eval   # retrieval evaluation
```

## Docker

```
docker build -t rag-assistant .
docker run -p 8000:8000 --env-file .env rag-assistant
```

Docs and indexes are built at image-build time, so containers start fast, but updating the docs requires a rebuild. The API key is injected at run time and is never baked into the image. The image was built and the `/ask` and `/stats` endpoints were verified locally in a container. **It is not deployed to any cloud service.**

## Limitations

- Eval set is small (16 answerable + 4 unanswerable), so results are directional, not statistically solid.
- Recall is measured at file level, so it is an upper bound on section-level recall.
- Eval questions were drafted with AI assistance; ground-truth files were then checked against the docs.
- Some chunks contain `{* ../../docs_src/... *}` placeholders instead of example code, so code-heavy answers may be weaker.
- Many sections are under 100 words, so chunk counts barely differ between sizes.
- 200-word chunks may exceed the embedding model's input limit and be truncated (not yet measured).
- `/stats` average confidence mixes refused and answered rows. Feedback is not de-duplicated per query.
- English docs only; answers depend on an external LLM API (Groq free tier).

## Next steps (not implemented)

Hybrid BM25 + dense retrieval, a reranker, section-level recall, and a larger eval set. Cloud deployment.