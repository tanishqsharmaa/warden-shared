"""Unit tests for OpenTelemetry distributed tracing and W3C context propagation."""
import pytest
from opentelemetry import trace

from warden_shared.telemetry.attributes import (
    MANDATORY_SPAN_ATTRIBUTES,
    SPAN_ATTR_CALLER_ROLE,
    SPAN_ATTR_CHUNKS_RERANKED,
    SPAN_ATTR_CHUNKS_RETRIEVED,
    SPAN_ATTR_LLM_TTFT_MS,
    SPAN_ATTR_QUERY_HASH,
    SPAN_ATTR_RERANK_FALLBACK,
    SPAN_ATTR_TRACE_ID,
)
from warden_shared.telemetry.propagation import (
    extract_w3c_trace_context,
    inject_w3c_trace_context,
)
from warden_shared.telemetry.tracer import (
    get_current_trace_and_span_id,
    init_tracer,
    trace_span,
)


@pytest.fixture(autouse=True)
def setup_telemetry():
    """Ensure clean tracer initialization before each test."""
    init_tracer("warden-unit-test")

def test_attributes_constants():
    assert SPAN_ATTR_TRACE_ID == "warden.trace_id"
    assert SPAN_ATTR_CALLER_ROLE == "warden.caller_role"
    assert SPAN_ATTR_QUERY_HASH == "warden.query_hash"
    assert SPAN_ATTR_CHUNKS_RETRIEVED == "warden.chunks_retrieved_count"
    assert SPAN_ATTR_CHUNKS_RERANKED == "warden.chunks_reranked_count"
    assert SPAN_ATTR_RERANK_FALLBACK == "warden.reranker_fallback_active"
    assert SPAN_ATTR_LLM_TTFT_MS == "warden.llm_time_to_first_token_ms"
    assert len(MANDATORY_SPAN_ATTRIBUTES) == 7

def test_get_current_trace_and_span_id_inactive():
    t_id, s_id = get_current_trace_and_span_id()
    assert t_id == ""
    assert s_id == ""

def test_trace_span_sync_decorator():
    @trace_span("test_sync_op", attributes={"test.env": "unit"})
    def sample_sync():
        t_id, s_id = get_current_trace_and_span_id()
        return t_id, s_id

    trace_id, span_id = sample_sync()
    assert len(trace_id) == 32
    assert len(span_id) == 16

@pytest.mark.asyncio
async def test_trace_span_async_decorator():
    @trace_span("test_async_op", attributes={"test.env": "unit"})
    async def sample_async():
        t_id, s_id = get_current_trace_and_span_id()
        return t_id, s_id

    trace_id, span_id = await sample_async()
    assert len(trace_id) == 32
    assert len(span_id) == 16

def test_trace_span_context_manager():
    with trace_span("test_cm_block", attributes={"block.id": 42}):
        trace_id, span_id = get_current_trace_and_span_id()
        assert len(trace_id) == 32
        assert len(span_id) == 16

    # Context should be closed outside the block
    after_t_id, after_s_id = get_current_trace_and_span_id()
    assert after_t_id == ""
    assert after_s_id == ""

def test_trace_span_records_exception():
    with pytest.raises(RuntimeError):
        with trace_span("failing_op"):
            raise RuntimeError("Deliberate failure for testing")

def test_w3c_trace_context_propagation():
    with trace_span("outbound_request_span"):
        headers: dict[str, str] = {}
        inject_w3c_trace_context(headers)
        assert "traceparent" in headers
        assert headers["traceparent"].startswith("00-")

        extracted_context = extract_w3c_trace_context(headers)
        assert extracted_context is not None

def test_w3c_trace_context_propagation_case_insensitive():
    raw_headers = {
        "Traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    }
    extracted_context = extract_w3c_trace_context(raw_headers)
    span = trace.get_current_span(extracted_context)
    ctx = span.get_span_context()
    assert ctx.is_valid
    assert format(ctx.trace_id, "032x") == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert format(ctx.span_id, "016x") == "00f067aa0ba902b7"

@pytest.mark.asyncio
async def test_trace_span_async_concurrent_invocations():
    import asyncio

    @trace_span("concurrent_op")
    async def task_worker(idx: int, delay: float) -> str:
        await asyncio.sleep(delay)
        t_id, s_id = get_current_trace_and_span_id()
        return s_id

    # Deliberately cause out-of-order entry and exit
    results = await asyncio.gather(
        task_worker(0, 0.05),
        task_worker(1, 0.01),
        task_worker(2, 0.04),
        task_worker(3, 0.02),
    )
    assert len(results) == 4
    assert len(set(results)) == 4

@pytest.mark.asyncio
async def test_trace_span_decorator_fresh_context():
    """Verify that decorator creates a new context per invocation, not sharing mutable state."""
    cm = trace_span("shared_dec")
    assert not hasattr(cm, "_cm") or cm._cm is None

    @cm
    def sync_fn():
        pass

    sync_fn()
    # After sync_fn completes, the decorator itself shouldn't hold onto a closed span
    assert getattr(cm, "_span", None) is None


