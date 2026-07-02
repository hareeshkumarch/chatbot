from dataclasses import dataclass


@dataclass(frozen=True)
class ApiKeyField:
    key: str
    label: str
    group: str
    secret: bool = True
    placeholder: str = ""


API_KEY_FIELDS: tuple[ApiKeyField, ...] = (
    ApiKeyField("anthropic_api_key", "Anthropic", "llm", placeholder="sk-ant-..."),
    ApiKeyField("openai_api_key", "OpenAI", "llm", placeholder="sk-..."),
    ApiKeyField("gemini_api_key", "Gemini", "llm", placeholder="AIza..."),
    ApiKeyField("groq_api_key", "Groq", "llm", placeholder="gsk_..."),
    ApiKeyField("xai_api_key", "xAI (Grok)", "llm", placeholder="xai-..."),
    ApiKeyField("moonshot_api_key", "Moonshot (Kimi)", "llm", placeholder="sk-..."),
    ApiKeyField("tavily_api_key", "Tavily", "intelligence", placeholder="tvly-..."),
    ApiKeyField("exa_api_key", "Exa", "intelligence", placeholder="..."),
    ApiKeyField("serper_api_key", "Serper", "intelligence", placeholder="..."),
    ApiKeyField("perplexity_api_key", "Perplexity", "intelligence", placeholder="pplx-..."),
    ApiKeyField("google_search_api_key", "Google Search API key", "intelligence", placeholder="AIza..."),
    ApiKeyField("google_search_engine_id", "Google Search Engine ID", "intelligence", secret=False, placeholder="cx..."),
    ApiKeyField("census_api_key", "US Census", "intelligence", placeholder="..."),
)

MANAGED_SECRET_KEYS: frozenset[str] = frozenset(field.key for field in API_KEY_FIELDS)
