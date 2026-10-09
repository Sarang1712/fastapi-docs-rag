import re, pathlib

def split_sections(text):
    """Yield (heading, body). Ignores '#' lines inside code fences."""
    heading, lines, in_code = "Introduction", [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,4} ", line):
            if any(l.strip() for l in lines):
                yield heading, "\n".join(lines)
            heading, lines = line.lstrip("# ").strip(), []
        else:
            lines.append(line)
    if any(l.strip() for l in lines):
        yield heading, "\n".join(lines)

def chunk_words(text, size, overlap):
    assert size > overlap, "overlap must be smaller than size"
    words = re.findall(r"\S+\s*", text)  # keeps newlines/spacing
    for start in range(0, max(len(words), 1), size - overlap):
        piece = "".join(words[start:start + size]).strip()
        if piece:
            yield piece
        if start + size >= len(words):
            break

def chunk_document(text, source, size, overlap=20):
    return [{"source": source, "heading": h, "text": p}
            for h, body in split_sections(text)
            for p in chunk_words(body, size, overlap)]

def load_chunks(size, overlap=20, root="data/docs"):
    chunks = []
    for path in sorted(pathlib.Path(root).rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks += chunk_document(text, path.relative_to(root).as_posix(), size, overlap)
    for i, c in enumerate(chunks):
        c["id"] = i
    return chunks