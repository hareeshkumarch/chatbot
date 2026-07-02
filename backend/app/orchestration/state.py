from dataclasses import dataclass, field
from typing import TypedDict

from app.connectors.base import BaseConnector
from app.connectors.database.sql_connector import SQLConnector
from app.llm.base import Message


class GraphState(TypedDict, total=False):
    tenant_id: str
    connector_ids: list[str]
    query: str
    history: list[Message]
    intent: str
    plan: list[dict]
    plan_results: list[dict]
    llm_calls: list[dict]
    answer: str
    citations: list[dict]
    provider_used: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    verified: bool
    synthesis_attempts: int
    error: str | None


@dataclass
class GraphContext:
    sql_connector: SQLConnector | None = None
    active_connectors: list[BaseConnector] = field(default_factory=list)
    explicit_provider: str | None = None
    explicit_model: str | None = None
