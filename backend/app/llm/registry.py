from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.grok_provider import GrokProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.moonshot_provider import MoonshotProvider
from app.llm.providers.openai_provider import OpenAIProvider

_instances: dict[str, LLMProvider] = {}

DEFAULT_MODELS: dict[str, str] = {}


def _build_registry() -> dict[str, LLMProvider]:
    settings = get_settings()
    registry: dict[str, LLMProvider] = {}
    if settings.anthropic_api_key:
        registry["anthropic"] = AnthropicProvider(settings.anthropic_api_key, settings.anthropic_base_url, settings.anthropic_version)
        DEFAULT_MODELS["anthropic"] = settings.anthropic_default_model
    if settings.openai_api_key:
        registry["openai"] = OpenAIProvider(settings.openai_api_key, settings.openai_base_url)
        DEFAULT_MODELS["openai"] = settings.openai_default_model
    if settings.gemini_api_key:
        registry["gemini"] = GeminiProvider(settings.gemini_api_key, settings.gemini_base_url)
        DEFAULT_MODELS["gemini"] = settings.gemini_default_model
    if settings.groq_api_key:
        registry["groq"] = GroqProvider(settings.groq_api_key, settings.groq_base_url)
        DEFAULT_MODELS["groq"] = settings.groq_default_model
    if settings.xai_api_key:
        registry["grok"] = GrokProvider(settings.xai_api_key, settings.xai_base_url)
        DEFAULT_MODELS["grok"] = settings.xai_default_model
    if settings.moonshot_api_key:
        registry["moonshot"] = MoonshotProvider(settings.moonshot_api_key, settings.moonshot_base_url)
        DEFAULT_MODELS["moonshot"] = settings.moonshot_default_model
    return registry


def get_provider_registry() -> dict[str, LLMProvider]:
    global _instances
    if not _instances:
        _instances = _build_registry()
    return _instances


def get_provider(name: str) -> LLMProvider:
    registry = get_provider_registry()
    if name not in registry:
        raise KeyError(f"provider '{name}' is not configured")
    return registry[name]


def available_providers() -> list[str]:
    return list(get_provider_registry().keys())


def reset_registry() -> None:
    global _instances
    _instances = {}
