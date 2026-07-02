from dataclasses import dataclass, field


@dataclass
class ReportTable:
    headers: list[str]
    rows: list[list[str]]


@dataclass
class ReportChart:
    title: str
    chart_type: str
    labels: list[str]
    series: dict[str, list[float]]


@dataclass
class ReportSection:
    heading: str
    paragraphs: list[str] = field(default_factory=list)
    table: ReportTable | None = None
    chart: ReportChart | None = None


@dataclass
class Report:
    title: str
    subtitle: str = ""
    sections: list[ReportSection] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)


def citation_label(citation: dict) -> str:
    return citation.get("title") or citation.get("source_uri") or "source"
