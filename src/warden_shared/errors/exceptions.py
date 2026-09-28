"""Standard Exception Hierarchy for Warden Platform.

Each exception maps to a canonical enterprise ErrorCode and RFC 7807 status.
"""
from datetime import datetime, timezone
from typing import Any

from .codes import ERROR_METADATA, ErrorCode
from .problem_details import InvalidParameter, RFC7807ProblemDetails


class WardenException(Exception):
    """Base exception for all operational and runtime errors in Warden."""

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str,
        status_code: int | None = None,
        title: str | None = None,
        type_uri: str | None = None,
        instance: str = "/",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
        *args: Any,
    ) -> None:
        super().__init__(detail, *args)
        self.error_code = error_code
        self.detail = detail
        default_status, default_title, default_type = ERROR_METADATA[error_code]
        self.status_code = status_code if status_code is not None else default_status
        self.title = title if title is not None else default_title
        self.type_uri = type_uri if type_uri is not None else default_type
        self.instance = instance
        self.invalid_parameters = invalid_parameters
        self.headers = headers

    def to_problem_details(self, instance: str | None = None) -> RFC7807ProblemDetails:
        """Serialize exception to an RFC 7807 compliant model."""
        return RFC7807ProblemDetails(
            type=self.type_uri,
            title=self.title,
            status=self.status_code,
            detail=self.detail,
            instance=instance or self.instance,
            error_code=self.error_code,
            invalid_parameters=self.invalid_parameters,
            timestamp=datetime.now(timezone.utc),
        )

class RoleMissingError(WardenException):
    """Client request lacks mandatory X-User-Role header (HTTP 401)."""

    def __init__(
        self,
        detail: str = "Client request lacks mandatory 'X-User-Role' header.",
        instance: str = "/",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_AUTH_ROLE_MISSING,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class RoleInvalidError(WardenException):
    """Client request role does not match permitted roles (HTTP 403)."""

    def __init__(
        self,
        detail: str = "Provided role does not match 'Employee', 'Manager', or 'HR-Admin'.",
        instance: str = "/",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_AUTH_ROLE_INVALID,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class IngestionFileCorruptError(WardenException):
    """Source file body is corrupted or unparseable (HTTP 422)."""

    def __init__(
        self,
        detail: str = "Document body contains unparseable syntax or invalid encoding.",
        instance: str = "/ingest/run",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_INGESTION_FILE_CORRUPT,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class PoisonPillQuarantinedError(WardenException):
    """Document repeatedly failed processing and was moved to DLQ (HTTP 422)."""

    def __init__(
        self,
        detail: str = "Document quarantined to Dead-Letter Queue after 3 failed attempts.",
        instance: str = "/ingest/run",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_POISON_PILL_QUARANTINED,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class QdrantUnavailableError(WardenException):
    """Qdrant vector datastore is unreachable or timed out (HTTP 503 Fails Closed)."""

    def __init__(
        self,
        detail: str = "Qdrant vector datastore connection failed or timed out.",
        instance: str = "/retrieve",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_QDRANT_UNAVAILABLE,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class CacheUnavailableError(WardenException):
    """Redis cache cluster is unreachable or timed out (HTTP 503 Degraded Warning)."""

    def __init__(
        self,
        detail: str = "Redis distributed cache is unreachable; live fallback active.",
        instance: str = "/query",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_CACHE_UNAVAILABLE,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class ConcurrencyLimitExceededError(WardenException):
    """Worker pod concurrency limit reached (HTTP 429)."""

    def __init__(
        self,
        detail: str = "Inference slots saturated (>16 concurrent requests). Retry after delay.",
        instance: str = "/rerank",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        effective_headers = headers if headers is not None else {"Retry-After": "0.1"}
        super().__init__(
            error_code=ErrorCode.ERR_CONCURRENCY_LIMIT_EXCEEDED,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=effective_headers,
        )

class LayaInferenceTimeoutError(WardenException):
    """ModernBERT decision inference exceeded 150ms deadline (HTTP 504)."""

    def __init__(
        self,
        detail: str = "ModernBERT decision inference exceeded 150ms speculative deadline.",
        instance: str = "/rerank",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_LAYA_INFERENCE_TIMEOUT,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )

class LLMGenerationFailedError(WardenException):
    """Azure OpenAI API quota exhausted, throttled (429), or down (HTTP 502)."""

    def __init__(
        self,
        detail: str = "Azure OpenAI generation failed or rate limit exceeded.",
        instance: str = "/query",
        invalid_parameters: list[InvalidParameter] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.ERR_LLM_GENERATION_FAILED,
            detail=detail,
            instance=instance,
            invalid_parameters=invalid_parameters,
            headers=headers,
        )
