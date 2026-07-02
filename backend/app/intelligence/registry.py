from app.config import get_settings
from app.intelligence.base import AnswerProvider, DemographicsProvider, FinanceProvider, SearchProvider, TrendsProvider
from app.intelligence.providers.census_provider import CensusDemographicsProvider
from app.intelligence.providers.exa_provider import ExaProvider
from app.intelligence.providers.google_search_provider import GoogleSearchProvider
from app.intelligence.providers.google_trends_provider import GoogleTrendsProvider
from app.intelligence.providers.perplexity_provider import PerplexityProvider
from app.intelligence.providers.serper_provider import SerperProvider
from app.intelligence.providers.tavily_provider import TavilyProvider
from app.intelligence.providers.yahoo_finance_provider import YahooFinanceProvider

_search_instances: dict[str, SearchProvider] = {}
_answer_instances: dict[str, AnswerProvider] = {}
_demographics_instances: dict[str, DemographicsProvider] = {}
_trends_instance: TrendsProvider | None = None
_finance_instance: FinanceProvider | None = None


def _build_search_registry() -> dict[str, SearchProvider]:
    settings = get_settings()
    registry: dict[str, SearchProvider] = {}
    if settings.tavily_api_key:
        registry["tavily"] = TavilyProvider(settings.tavily_api_key)
    if settings.exa_api_key:
        registry["exa"] = ExaProvider(settings.exa_api_key)
    if settings.serper_api_key:
        registry["serper"] = SerperProvider(settings.serper_api_key)
    if settings.google_search_api_key and settings.google_search_engine_id:
        registry["google_search"] = GoogleSearchProvider(settings.google_search_api_key, settings.google_search_engine_id)
    return registry


def get_search_providers() -> dict[str, SearchProvider]:
    global _search_instances
    if not _search_instances:
        _search_instances = _build_search_registry()
    return _search_instances


def get_serper_provider() -> SerperProvider | None:
    provider = get_search_providers().get("serper")
    return provider if isinstance(provider, SerperProvider) else None


def _build_answer_registry() -> dict[str, AnswerProvider]:
    settings = get_settings()
    registry: dict[str, AnswerProvider] = {}
    if settings.perplexity_api_key:
        registry["perplexity"] = PerplexityProvider(settings.perplexity_api_key, settings.perplexity_model)
    return registry


def get_answer_providers() -> dict[str, AnswerProvider]:
    global _answer_instances
    if not _answer_instances:
        _answer_instances = _build_answer_registry()
    return _answer_instances


def _build_demographics_registry() -> dict[str, DemographicsProvider]:
    settings = get_settings()
    registry: dict[str, DemographicsProvider] = {}
    if settings.census_api_key:
        registry["census"] = CensusDemographicsProvider(settings.census_api_key)
    return registry


def get_demographics_providers() -> dict[str, DemographicsProvider]:
    global _demographics_instances
    if not _demographics_instances:
        _demographics_instances = _build_demographics_registry()
    return _demographics_instances


def get_trends_provider() -> TrendsProvider:
    global _trends_instance
    if _trends_instance is None:
        _trends_instance = GoogleTrendsProvider()
    return _trends_instance


def get_finance_provider() -> FinanceProvider:
    global _finance_instance
    if _finance_instance is None:
        _finance_instance = YahooFinanceProvider()
    return _finance_instance


def reset_intelligence_registry() -> None:
    global _search_instances, _answer_instances, _demographics_instances, _trends_instance, _finance_instance
    _search_instances = {}
    _answer_instances = {}
    _demographics_instances = {}
    _trends_instance = None
    _finance_instance = None
