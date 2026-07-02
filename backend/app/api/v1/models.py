from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.circuit_breaker import get_circuit_breaker
from app.dependencies import AuthContext, get_current_user
from app.llm.model_catalog import PROVIDER_MODEL_CATALOG, models_for_provider
from app.llm.registry import DEFAULT_MODELS, available_providers, get_provider_registry
from app.llm.router import TASK_DEFAULT_TEMPERATURE, TASK_ROUTING_TABLE

router = APIRouter(prefix="/models", tags=["models"])


class ProviderOut(BaseModel):
    provider: str
    default_model: str
    circuit_state: str


class TaskRoutingOut(BaseModel):
    task: str
    fallback_chain: list[str]
    default_temperature: float


class ModelOptionOut(BaseModel):
    id: str
    label: str
    tier: str
    is_default: bool


class ProviderModelsOut(BaseModel):
    provider: str
    default_model: str
    circuit_state: str | None
    configured: bool
    models: list[ModelOptionOut]


class ModelCatalogOut(BaseModel):
    providers: list[ProviderModelsOut]


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(auth: AuthContext = Depends(get_current_user)) -> list[ProviderOut]:
    get_provider_registry()
    providers = available_providers()
    return [
        ProviderOut(
            provider=name,
            default_model=DEFAULT_MODELS.get(name, ""),
            circuit_state=get_circuit_breaker(f"llm:{name}").state.value,
        )
        for name in providers
    ]


@router.get("/tasks", response_model=list[TaskRoutingOut])
async def list_task_routing(auth: AuthContext = Depends(get_current_user)) -> list[TaskRoutingOut]:
    configured = set(available_providers())
    return [
        TaskRoutingOut(
            task=task.value,
            fallback_chain=[p for p in chain if p in configured],
            default_temperature=TASK_DEFAULT_TEMPERATURE[task],
        )
        for task, chain in TASK_ROUTING_TABLE.items()
    ]


@router.get("/catalog", response_model=ModelCatalogOut)
async def list_model_catalog(auth: AuthContext = Depends(get_current_user)) -> ModelCatalogOut:
    get_provider_registry()
    configured = set(available_providers())
    providers: list[ProviderModelsOut] = []
    for name in PROVIDER_MODEL_CATALOG:
        is_configured = name in configured
        default_model = DEFAULT_MODELS.get(name, "")
        if not default_model:
            catalog_models = PROVIDER_MODEL_CATALOG.get(name, ())
            default_model = catalog_models[0].id if catalog_models else ""
        models = models_for_provider(name, default_model)
        providers.append(
            ProviderModelsOut(
                provider=name,
                default_model=default_model,
                circuit_state=get_circuit_breaker(f"llm:{name}").state.value if is_configured else None,
                configured=is_configured,
                models=[
                    ModelOptionOut(
                        id=model.id,
                        label=model.label,
                        tier=model.tier,
                        is_default=model.id == default_model,
                    )
                    for model in models
                ],
            )
        )
    return ModelCatalogOut(providers=providers)
