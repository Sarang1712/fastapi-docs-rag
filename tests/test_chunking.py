from app.chunking import chunk_words, split_sections
from app.retrieval import is_confident

def test_chunk_words_size_and_overlap():
    text = " ".join(str(i) for i in range(100))
    chunks = list(chunk_words(text, 50, 10))
    assert all(len(c.split()) <= 50 for c in chunks)
    assert chunks[1].split()[0] == "40"   # step = 50 - 10

def test_split_sections_ignores_hash_in_code_fence():
    text = "# Title\nintro\n```\n# not a heading\n```\n## Real\nbody"
    headings = [h for h, _ in split_sections(text)]
    assert any("Real" in h for h in headings)
    assert not any("not a heading" in h for h in headings)

def test_is_confident_threshold():
    assert is_confident([{"score": 0.50}]) is True
    assert is_confident([{"score": 0.40}]) is False
    assert is_confident([]) is False