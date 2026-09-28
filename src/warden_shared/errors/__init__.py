"""Warden Error Hierarchy and RFC 7807 Problem Details."""
from .codes import ERROR_METADATA, ErrorCode
from .exceptions import (
    CacheUnavailableError,
    ConcurrencyLimitExceededError,
    IngestionFileCorruptError,
    LayaInferenceTimeoutError,
    LLMGenerationFailedError,
    PoisonPillQuarantinedError,
    QdrantUnavailableError,
    RoleInvalidError,
    RoleMissingError,
    WardenException,
)
from .handlers import register_error_handlers
from .problem_details import InvalidParameter, RFC7807ProblemDetails

__all__ = [
    "ErrorCode",
    "ERROR_METADATA",
    "InvalidParameter",
    "RFC7807ProblemDetails",
    "register_error_handlers",
    "WardenException",
    "RoleMissingError",
    "RoleInvalidError",
    "IngestionFileCorruptError",
    "PoisonPillQuarantinedError",
    "QdrantUnavailableError",
    "CacheUnavailableError",
    "ConcurrencyLimitExceededError",
    "LayaInferenceTimeoutError",
    "LLMGenerationFailedError",
]
