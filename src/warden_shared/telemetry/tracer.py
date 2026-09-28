"""OpenTelemetry Tracing Decorators and Management Utilities."""
import functools
import inspect
from typing import Any, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import StatusCode, Tracer

F = TypeVar("F", bound=Callable[..., Any])

def init_tracer(service_name: str, otlp_endpoint: str | None = None) -> Tracer:
    """Initialize OpenTelemetry TracerProvider with service resource."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except ImportError:
            pass
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

def get_tracer(service_name: str = "warden") -> Tracer:
    """Get or create a tracer for the given service name."""
    return trace.get_tracer(service_name)

def get_current_trace_and_span_id() -> tuple[str, str]:
    """Return the current active (trace_id, span_id) hex strings or ('', '')."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return "", ""
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")

class _TraceSpanContextManager:
    """Context manager and decorator supporting sync and async functions."""

    def __init__(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        tracer_name: str = "warden",
    ) -> None:
        self.name = name
        self.attributes = attributes or {}
        self.tracer_name = tracer_name
        self._cm: Any = None
        self._span: Any = None

    def __enter__(self) -> trace.Span:
        tracer = get_tracer(self.tracer_name)
        self._cm = tracer.start_as_current_span(self.name)
        self._span = self._cm.__enter__()
        for k, v in self.attributes.items():
            self._span.set_attribute(k, v)
        return self._span  # type: ignore[no-any-return]

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        try:
            if exc_val is not None and self._span is not None:
                self._span.record_exception(exc_val)
                self._span.set_status(StatusCode.ERROR, str(exc_val))
            if self._cm is not None:
                return self._cm.__exit__(exc_type, exc_val, exc_tb)
            return False
        finally:
            self._span = None
            self._cm = None

    def __call__(self, fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with trace_span(self.name, self.attributes, self.tracer_name):
                    return await fn(*args, **kwargs)
            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with trace_span(self.name, self.attributes, self.tracer_name):
                    return fn(*args, **kwargs)
            return sync_wrapper  # type: ignore[return-value]

def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    tracer_name: str = "warden",
) -> _TraceSpanContextManager:
    """Trace a block of code or function (sync or async) with OpenTelemetry."""
    return _TraceSpanContextManager(name=name, attributes=attributes, tracer_name=tracer_name)
