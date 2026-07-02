import hashlib
import re


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return re.split(r"(?<=[.!?])\s+", text)


def chunk_text(text: str, chunk_size_tokens: int = 512, overlap_tokens: int = 64) -> list[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return []
    chunk_size_chars = chunk_size_tokens * 4
    overlap_chars = overlap_tokens * 4
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            overlap_text = current[-overlap_chars:] if overlap_chars < len(current) else current
            current = f"{overlap_text} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def chunk_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
