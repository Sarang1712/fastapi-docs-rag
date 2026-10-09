import re, json, pathlib
import numpy as np, faiss
from sentence_transformers import SentenceTransformer
from app.chunking import load_chunks

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed(texts):
    vecs = get_model().encode(texts, normalize_embeddings=True,
                              batch_size=64, show_progress_bar=len(texts) > 100)
    return np.asarray(vecs, dtype="float32")

def clean_heading(h):
    return re.sub(r"\s*\{\s*#[^}]*\}", "", h).strip()

def build_index(size, overlap=20):
    chunks = load_chunks(size, overlap)
    vecs = embed([f"{clean_heading(c['heading'])}\n{c['text']}" for c in chunks])
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, f"data/index_{size}.faiss")
    pathlib.Path(f"data/chunks_{size}.json").write_text(
        json.dumps(chunks), encoding="utf-8")
    print(size, "chunks:", len(chunks), "vectors:", index.ntotal, "dim:", vecs.shape[1])

if __name__ == "__main__":
    for s in (100, 200):
        build_index(s)