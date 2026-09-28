"""W3C Trace Context Propagation Utilities."""
from typing import Mapping, MutableMapping

from opentelemetry.context.context import Context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_PROPAGATOR = TraceContextTextMapPropagator()

def inject_w3c_trace_context(
    carrier: MutableMapping[str, str],
    context: Context | None = None,
) -> MutableMapping[str, str]:
    """Inject W3C traceparent and tracestate into the carrier dictionary."""
    _PROPAGATOR.inject(carrier=carrier, context=context)
    return carrier

def extract_w3c_trace_context(
    carrier: Mapping[str, str],
    context: Context | None = None,
) -> Context:
    """Extract OpenTelemetry Context from carrier containing W3C trace headers."""
    normalized = {k.lower(): v for k, v in carrier.items()}
    return _PROPAGATOR.extract(carrier=normalized, context=context)
