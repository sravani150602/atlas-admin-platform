"""No identities, prompts, cookies or email addresses are attached to spans."""
import os
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

def configure(name):
    resource = Resource.create({"service.name": name, "service.version": "1.0.0"})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[
            PeriodicExportingMetricReader(OTLPMetricExporter())]))
    return trace.get_tracer(name)
