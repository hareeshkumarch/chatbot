from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    label: str
    tier: str


PROVIDER_MODEL_CATALOG: dict[str, tuple[ModelDefinition, ...]] = {
    "anthropic": (
        ModelDefinition("claude-opus-4-8", "Claude Opus 4.8", "flagship"),
        ModelDefinition("claude-sonnet-5", "Claude Sonnet 5", "balanced"),
        ModelDefinition("claude-4.5-sonnet", "Claude 4.5 Sonnet", "balanced"),
        ModelDefinition("claude-4.5-haiku", "Claude 4.5 Haiku", "fast"),
        ModelDefinition("claude-3-5-haiku-20241022", "Claude 3.5 Haiku", "fast"),
    ),
    "openai": (
        ModelDefinition("gpt-5.5", "GPT-5.5", "flagship"),
        ModelDefinition("gpt-5.5-medium", "GPT-5.5 Medium", "balanced"),
        ModelDefinition("gpt-5.5-mini", "GPT-5.5 Mini", "fast"),
        ModelDefinition("gpt-5.1", "GPT-5.1", "balanced"),
        ModelDefinition("o4-mini", "o4-mini", "reasoning"),
        ModelDefinition("o3", "o3", "reasoning"),
    ),
    "gemini": (
        ModelDefinition("gemini-3.5-flash", "Gemini 3.5 Flash", "fast"),
        ModelDefinition("gemini-3-pro", "Gemini 3 Pro", "flagship"),
        ModelDefinition("gemini-2.5-pro", "Gemini 2.5 Pro", "balanced"),
        ModelDefinition("gemini-2.5-flash", "Gemini 2.5 Flash", "fast"),
    ),
    "groq": (
        ModelDefinition("openai/gpt-oss-120b", "GPT-OSS 120B", "flagship"),
        ModelDefinition("llama-3.3-70b-versatile", "Llama 3.3 70B", "balanced"),
        ModelDefinition("llama-3.1-70b-versatile", "Llama 3.1 70B", "balanced"),
        ModelDefinition("llama-3.1-8b-instant", "Llama 3.1 8B Instant", "fast"),
        ModelDefinition("mixtral-8x7b-32768", "Mixtral 8x7B", "fast"),
        ModelDefinition("gemma2-9b-it", "Gemma 2 9B", "fast"),
    ),
    "grok": (
        ModelDefinition("grok-4.3", "Grok 4.3", "flagship"),
        ModelDefinition("grok-3", "Grok 3", "balanced"),
        ModelDefinition("grok-3-mini", "Grok 3 Mini", "fast"),
    ),
    "moonshot": (
        ModelDefinition("kimi-k2.6", "Kimi K2.6", "flagship"),
        ModelDefinition("kimi-k2.5", "Kimi K2.5", "balanced"),
        ModelDefinition("moonshot-v1-128k", "Moonshot v1 128K", "balanced"),
        ModelDefinition("moonshot-v1-32k", "Moonshot v1 32K", "fast"),
    ),
}


def models_for_provider(provider: str, default_model: str) -> list[ModelDefinition]:
    catalog = list(PROVIDER_MODEL_CATALOG.get(provider, ()))
    if default_model and not any(model.id == default_model for model in catalog):
        catalog.insert(0, ModelDefinition(default_model, default_model, "default"))
    return catalog
