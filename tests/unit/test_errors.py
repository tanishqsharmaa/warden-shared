"""Unit tests for RFC 7807 Problem Details and Exception Hierarchy."""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from warden_shared.errors.codes import ERROR_METADATA, ErrorCode
from warden_shared.errors.exceptions import (
    CacheUnavailableError,
    ConcurrencyLimitExceededError,
    IngestionFileCorruptError,
    LayaInferenceTimeoutError,
    LLMGenerationFailedError,
    PoisonPillQuarantinedError,
    QdrantUnavailableError,
    RoleInvalidError,
    RoleMissingError,
)
from warden_shared.errors.handlers import register_error_handlers
from warden_shared.errors.problem_details import InvalidParameter, RFC7807ProblemDetails


def test_problem_details_schema_compliance():
    pd = RFC7807ProblemDetails(
        type="https://warden.enterprise/errors/auth-role-invalid",
        title="Invalid User Role",
        status=403,
        detail="Role 'Contractor' is not permitted.",
        instance="/query",
        error_code=ErrorCode.ERR_AUTH_ROLE_INVALID,
        timestamp=datetime.now(timezone.utc),
    )
    data = pd.model_dump(mode="json")
    assert data["status"] == 403
    assert data["error_code"] == "ERR_AUTH_ROLE_INVALID"
    assert data["type"] == "https://warden.enterprise/errors/auth-role-invalid"
    assert data["title"] == "Invalid User Role"
    assert "timestamp" in data

def test_problem_details_invalid_parameters_serialization():
    pd = RFC7807ProblemDetails(
        type="https://warden.enterprise/errors/auth-role-missing",
        title="Missing Header",
        status=401,
        detail="Header missing",
        instance="/query",
        error_code=ErrorCode.ERR_AUTH_ROLE_MISSING,
        invalid_parameters=[
            InvalidParameter(name="X-User-Role", reason="Header required"),
            InvalidParameter(name="X-Tenant-ID", reason="Tenant header missing"),
        ],
        timestamp=datetime.now(timezone.utc),
    )
    data = pd.model_dump(mode="json")
    assert len(data["invalid_parameters"]) == 2
    assert data["invalid_parameters"][0]["name"] == "X-User-Role"
    assert data["invalid_parameters"][0]["reason"] == "Header required"

def test_all_9_enterprise_exceptions():
    exceptions = [
        (RoleMissingError(), ErrorCode.ERR_AUTH_ROLE_MISSING, 401),
        (RoleInvalidError(), ErrorCode.ERR_AUTH_ROLE_INVALID, 403),
        (IngestionFileCorruptError(), ErrorCode.ERR_INGESTION_FILE_CORRUPT, 422),
        (PoisonPillQuarantinedError(), ErrorCode.ERR_POISON_PILL_QUARANTINED, 422),
        (QdrantUnavailableError(), ErrorCode.ERR_QDRANT_UNAVAILABLE, 503),
        (CacheUnavailableError(), ErrorCode.ERR_CACHE_UNAVAILABLE, 503),
        (ConcurrencyLimitExceededError(), ErrorCode.ERR_CONCURRENCY_LIMIT_EXCEEDED, 429),
        (LayaInferenceTimeoutError(), ErrorCode.ERR_LAYA_INFERENCE_TIMEOUT, 504),
        (LLMGenerationFailedError(), ErrorCode.ERR_LLM_GENERATION_FAILED, 502),
    ]

    for exc, expected_code, expected_status in exceptions:
        assert exc.error_code == expected_code
        assert exc.status_code == expected_status
        assert exc.type_uri == ERROR_METADATA[expected_code][2]
        pd = exc.to_problem_details(instance="/test-path")
        assert pd.status == expected_status
        assert pd.error_code == expected_code
        assert pd.instance == "/test-path"

@pytest.mark.asyncio
async def test_fastapi_warden_exception_handler():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/trigger-role-missing")
    async def trigger_role_missing():
        raise RoleMissingError(
            detail="Header X-User-Role is absent",
            instance="/trigger-role-missing",
        )

    @app.get("/trigger-unhandled")
    async def trigger_unhandled():
        raise ValueError("Unexpected database corruption")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test WardenException
        resp = await client.get("/trigger-role-missing")
        assert resp.status_code == 401
        assert resp.headers["content-type"] == "application/problem+json"
        data = resp.json()
        assert data["error_code"] == "ERR_AUTH_ROLE_MISSING"
        assert data["status"] == 401
        assert data["instance"] == "/trigger-role-missing"
        assert data["detail"] == "Header X-User-Role is absent"

        # Test Unhandled Exception fallback
        resp2 = await client.get("/trigger-unhandled")
        assert resp2.status_code == 500
        assert resp2.headers["content-type"] == "application/problem+json"
        data2 = resp2.json()
        assert data2["status"] == 500
        assert data2["title"] == "Internal Server Error"
        # Must not leak raw exception message
        assert data2["detail"] == "An unexpected internal server error occurred."
        assert "Unexpected database corruption" not in data2["detail"]

@pytest.mark.asyncio
async def test_fastapi_warden_exception_custom_headers():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/trigger-throttled")
    async def trigger_throttled():
        raise ConcurrencyLimitExceededError(
            detail="Inference slots saturated",
            instance="/trigger-throttled",
            headers={"Retry-After": "0.1"},
        )

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/trigger-throttled")
        assert resp.status_code == 429
        assert resp.headers.get("retry-after") == "0.1"

def test_problem_details_excludes_none_invalid_parameters():
    pd = RFC7807ProblemDetails(
        type="https://warden.enterprise/errors/auth-role-missing",
        title="Missing Header",
        status=401,
        detail="Header missing",
        instance="/query",
        error_code=ErrorCode.ERR_AUTH_ROLE_MISSING,
        invalid_parameters=None,
        timestamp=datetime.now(timezone.utc),
    )
    data = pd.model_dump(mode="json", exclude_none=True)
    assert "invalid_parameters" not in data

