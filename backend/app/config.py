from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    encryption_key: str = "0" * 44

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_ai"
    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    anthropic_api_key: str | None = None
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_default_model: str = "claude-sonnet-5"
    anthropic_version: str = "2023-06-01"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-5.5"

    gemini_api_key: str | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_default_model: str = "gemini-3.5-flash"

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_default_model: str = "openai/gpt-oss-120b"

    xai_api_key: str | None = None
    xai_base_url: str = "https://api.x.ai/v1"
    xai_default_model: str = "grok-4.3"

    moonshot_api_key: str | None = None
    moonshot_base_url: str = "https://api.moonshot.ai/v1"
    moonshot_default_model: str = "kimi-k2.6"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_enabled: bool = True

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    azure_storage_connection_string: str | None = None

    gcp_service_account_json: str | None = None
    gcp_project_id: str | None = None

    slack_client_id: str | None = None
    slack_client_secret: str | None = None
    slack_redirect_uri: str = "http://localhost:8000/api/v1/connectors/slack/callback"

    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_redirect_uri: str = "http://localhost:8000/api/v1/connectors/github/callback"

    jira_client_id: str | None = None
    jira_client_secret: str | None = None
    jira_redirect_uri: str = "http://localhost:8000/api/v1/connectors/jira/callback"

    confluence_redirect_uri: str = "http://localhost:8000/api/v1/connectors/confluence/callback"

    notion_client_id: str | None = None
    notion_client_secret: str | None = None
    notion_redirect_uri: str = "http://localhost:8000/api/v1/connectors/notion/callback"

    google_drive_client_id: str | None = None
    google_drive_client_secret: str | None = None
    google_drive_redirect_uri: str = "http://localhost:8000/api/v1/connectors/google_drive/callback"

    dropbox_client_id: str | None = None
    dropbox_client_secret: str | None = None
    dropbox_redirect_uri: str = "http://localhost:8000/api/v1/connectors/dropbox/callback"

    zendesk_client_id: str | None = None
    zendesk_client_secret: str | None = None
    zendesk_redirect_uri: str = "http://localhost:8000/api/v1/connectors/zendesk/callback"

    otel_exporter_endpoint: str | None = None
    otel_service_name: str = "enterprise-ai-platform"
    otel_enabled: bool = False

    phoenix_enabled: bool = False
    phoenix_collector_endpoint: str = "http://phoenix:6006/v1/traces"
    phoenix_project_name: str = "enterprise-ai-platform"
    phoenix_ui_url: str = "http://localhost:6006"

    small_corpus_threshold: int = 1000
    large_corpus_threshold: int = 100000

    max_upload_mb: int = 100
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64

    semantic_cache_similarity_threshold: float = 0.96
    semantic_cache_ttl_seconds: int = 3600

    sql_agent_row_limit: int = 500
    sql_agent_timeout_seconds: int = 15

    tavily_api_key: str | None = None
    exa_api_key: str | None = None
    serper_api_key: str | None = None
    perplexity_api_key: str | None = None
    perplexity_model: str = "sonar-pro"
    google_search_api_key: str | None = None
    google_search_engine_id: str | None = None
    census_api_key: str | None = None


_runtime_overrides: dict[str, str] = {}


@lru_cache
def _load_env_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    if not _runtime_overrides:
        return _load_env_settings()
    return _load_env_settings().model_copy(update=_runtime_overrides)


def apply_runtime_overrides(overrides: dict[str, str]) -> None:
    global _runtime_overrides
    _runtime_overrides = overrides


def update_runtime_overrides(updates: dict[str, str | None]) -> None:
    global _runtime_overrides
    for key, value in updates.items():
        if value is None or value.strip() == "":
            _runtime_overrides.pop(key, None)
        else:
            _runtime_overrides[key] = value.strip()
    refresh_provider_caches()


def refresh_provider_caches() -> None:
    from app.intelligence.registry import reset_intelligence_registry
    from app.llm.registry import reset_registry
    from app.retrieval.embeddings import reset_embedding_provider

    reset_registry()
    reset_intelligence_registry()
    reset_embedding_provider()
