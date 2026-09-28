"""Mandatory OpenTelemetry Span Attributes for Warden Platform.

Denormalized from ARCHITECTURE_SPECIFICATION.md § 3.2.
"""

SPAN_ATTR_TRACE_ID: str = "warden.trace_id"
SPAN_ATTR_CALLER_ROLE: str = "warden.caller_role"
SPAN_ATTR_QUERY_HASH: str = "warden.query_hash"
SPAN_ATTR_CHUNKS_RETRIEVED: str = "warden.chunks_retrieved_count"
SPAN_ATTR_CHUNKS_RERANKED: str = "warden.chunks_reranked_count"
SPAN_ATTR_RERANK_FALLBACK: str = "warden.reranker_fallback_active"
SPAN_ATTR_LLM_TTFT_MS: str = "warden.llm_time_to_first_token_ms"

MANDATORY_SPAN_ATTRIBUTES: list[str] = [
    SPAN_ATTR_TRACE_ID,
    SPAN_ATTR_CALLER_ROLE,
    SPAN_ATTR_QUERY_HASH,
    SPAN_ATTR_CHUNKS_RETRIEVED,
    SPAN_ATTR_CHUNKS_RERANKED,
    SPAN_ATTR_RERANK_FALLBACK,
    SPAN_ATTR_LLM_TTFT_MS,
]
