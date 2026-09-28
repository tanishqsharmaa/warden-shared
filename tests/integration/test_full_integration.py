"""Integration test asserting end-to-end inter-module operability across warden-shared."""
import json
import logging
from datetime import datetime, timezone

import pytest

import warden_shared
from warden_shared.cache import (
    CacheInvalidationEvent,
    format_lock_key,
    format_pubsub_channel,
    format_query_cache_key,
    normalize_query,
)
from warden_shared.errors import (
    ErrorCode,
    RFC7807ProblemDetails,
    RoleInvalidError,
)
from warden_shared.logging import WardenJSONFormatter
from warden_shared.proto.v1 import (
    laya_pb2_grpc,
    retrieval_pb2,
    retrieval_pb2_grpc,
)
from warden_shared.telemetry import (
    SPAN_ATTR_CALLER_ROLE,
    SPAN_ATTR_TRACE_ID,
    get_current_trace_and_span_id,
    init_tracer,
    inject_w3c_trace_context,
    trace_span,
)


def test_full_package_exports():
    """Verify package top-level and submodule symbols."""
    assert warden_shared.__version__ == "1.0.0"
    assert ErrorCode.ERR_AUTH_ROLE_MISSING.value == "ERR_AUTH_ROLE_MISSING"
    assert SPAN_ATTR_TRACE_ID == "warden.trace_id"
    assert hasattr(retrieval_pb2_grpc, "RetrievalServiceStub")
    assert hasattr(laya_pb2_grpc, "LayaInferenceServiceStub")

@pytest.mark.asyncio
async def test_composite_end_to_end_flow():
    """Simulate a complete microservice lifecycle using warden-shared primitives."""
    init_tracer("warden-e2e-service")
    formatter = WardenJSONFormatter(service_name="warden-e2e-service")

    query_raw = "   How many PTO days do full-time employees receive?  \n"
    normalized_q = normalize_query(query_raw)
    cache_key = format_query_cache_key("Employee", query_raw)
    lock_key = format_lock_key("Employee", query_raw)
    channel = format_pubsub_channel("Employee", query_raw)

    assert cache_key.startswith("cache:query:Employee:")
    assert lock_key.startswith("lock:query:Employee:")
    assert channel.startswith("channel:query:Employee:")

    # 1. Trace an inbound request
    headers: dict[str, str] = {}
    with trace_span("orchestrate_query", attributes={SPAN_ATTR_CALLER_ROLE: "Employee"}):
        current_trace, current_span = get_current_trace_and_span_id()
        assert len(current_trace) == 32
        assert len(current_span) == 16

        # 2. Inject W3C headers for downstream RPC
        inject_w3c_trace_context(headers)
        assert "traceparent" in headers
        assert current_trace in headers["traceparent"]

        # 3. Log a correlated message
        log_record = logging.LogRecord(
            name="warden.e2e",
            level=logging.INFO,
            pathname="flow.py",
            lineno=42,
            msg="Query received and cached keys generated",
            args=(),
            exc_info=None,
        )
        formatted_json = formatter.format(log_record)
        log_data = json.loads(formatted_json)
        assert log_data["trace_id"] == current_trace
        assert log_data["span_id"] == current_span
        assert log_data["service"] == "warden-e2e-service"

        # 4. Construct Protobuf retrieval request
        proto_req = retrieval_pb2.RetrieveRequest(
            query_text=normalized_q,
            caller_role="Employee",
            top_k_candidates=30,
            final_rerank_limit=5,
            enable_reranker=True,
        )
        binary_payload = proto_req.SerializeToString()
        assert len(binary_payload) > 0

    # 5. Invalidation event validation
    event = CacheInvalidationEvent(
        event="INGESTION_COMPLETED",
        run_id="run-e2e-001",
        affected_roles=["Employee"],
        timestamp=datetime.now(timezone.utc),
    )
    assert event.event == "INGESTION_COMPLETED"

    # 6. Error conversion to RFC 7807 problem details
    exc = RoleInvalidError(detail="Role 'Contractor' is forbidden", instance="/query")
    pd = exc.to_problem_details()
    assert isinstance(pd, RFC7807ProblemDetails)
    assert pd.status == 403
    assert pd.error_code == ErrorCode.ERR_AUTH_ROLE_INVALID
