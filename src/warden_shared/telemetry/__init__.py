"""Warden OpenTelemetry Telemetry and W3C Distributed Tracing Utilities."""
from .attributes import (
    MANDATORY_SPAN_ATTRIBUTES,
    SPAN_ATTR_CALLER_ROLE,
    SPAN_ATTR_CHUNKS_RERANKED,
    SPAN_ATTR_CHUNKS_RETRIEVED,
    SPAN_ATTR_LLM_TTFT_MS,
    SPAN_ATTR_QUERY_HASH,
    SPAN_ATTR_RERANK_FALLBACK,
    SPAN_ATTR_TRACE_ID,
)
from .propagation import extract_w3c_trace_context, inject_w3c_trace_context
from .tracer import get_current_trace_and_span_id, get_tracer, init_tracer, trace_span

__all__ = [
    "SPAN_ATTR_TRACE_ID",
    "SPAN_ATTR_CALLER_ROLE",
    "SPAN_ATTR_QUERY_HASH",
    "SPAN_ATTR_CHUNKS_RETRIEVED",
    "SPAN_ATTR_CHUNKS_RERANKED",
    "SPAN_ATTR_RERANK_FALLBACK",
    "SPAN_ATTR_LLM_TTFT_MS",
    "MANDATORY_SPAN_ATTRIBUTES",
    "init_tracer",
    "get_tracer",
    "get_current_trace_and_span_id",
    "trace_span",
    "inject_w3c_trace_context",
    "extract_w3c_trace_context",
]
