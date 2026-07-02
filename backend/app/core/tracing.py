from fastapi import FastAPI

from app.config import get_settings
from app.core.phoenix_tracing import mark_phoenix_ready


def configure_tracing(app: FastAPI) -> None:
    settings = get_settings()

    if settings.phoenix_enabled:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from phoenix.otel import register

        register(
            project_name=settings.phoenix_project_name,
            endpoint=settings.phoenix_collector_endpoint,
            batch=True,
        )
        FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/metrics")
        mark_phoenix_ready()
        return

    if not settings.otel_enabled:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    if settings.otel_exporter_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str):
    from opentelemetry import trace
    return trace.get_tracer(name)
