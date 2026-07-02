from bs4 import BeautifulSoup


def parse_html(raw_bytes: bytes) -> list[tuple[str, int | None]]:
    soup = BeautifulSoup(raw_bytes, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)
    return [(cleaned, None)]
