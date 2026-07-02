import csv
import io


def parse_csv(raw_bytes: bytes) -> list[tuple[str, int | None]]:
    text = raw_bytes.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    header = rows[0]
    blocks: list[str] = []
    batch_size = 40
    for start in range(1, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        lines = []
        for row in batch:
            pairs = [f"{header[i] if i < len(header) else f'col{i}'}: {value}" for i, value in enumerate(row)]
            lines.append(" | ".join(pairs))
        blocks.append("\n".join(lines))
    return [(block, None) for block in blocks]
