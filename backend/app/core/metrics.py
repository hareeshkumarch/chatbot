from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

queries_total = Counter("queries_total", "Total queries processed", ["tenant_id", "status"])
llm_requests_total = Counter("llm_requests_total", "Total LLM provider calls", ["provider", "model", "status"])
llm_latency_seconds = Histogram("llm_latency_seconds", "LLM call latency", ["provider", "model"])
retrieval_latency_seconds = Histogram("retrieval_latency_seconds", "Retrieval pipeline latency", ["strategy"])
retrieval_hit_count = Histogram("retrieval_hit_count", "Number of chunks retrieved per query", ["strategy"])
connector_sync_total = Counter("connector_sync_total", "Connector sync runs", ["connector_type", "status"])
active_connectors = Gauge("active_connectors", "Currently connected connectors", ["tenant_id"])
tokens_used_total = Counter("tokens_used_total", "Total tokens used", ["provider", "kind"])


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
