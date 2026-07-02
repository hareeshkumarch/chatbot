def parse_text(raw_bytes: bytes) -> list[tuple[str, int | None]]:
    text = raw_bytes.decode("utf-8", errors="ignore")
    return [(text, None)]
