"""Standard Enterprise Error Classification Codes for Warden Platform.

Denormalized from ARCHITECTURE_SPECIFICATION.md § 2.3.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """The 9 canonical enterprise error codes."""

    ERR_AUTH_ROLE_MISSING = "ERR_AUTH_ROLE_MISSING"
    ERR_AUTH_ROLE_INVALID = "ERR_AUTH_ROLE_INVALID"
    ERR_INGESTION_FILE_CORRUPT = "ERR_INGESTION_FILE_CORRUPT"
    ERR_POISON_PILL_QUARANTINED = "ERR_POISON_PILL_QUARANTINED"
    ERR_QDRANT_UNAVAILABLE = "ERR_QDRANT_UNAVAILABLE"
    ERR_CACHE_UNAVAILABLE = "ERR_CACHE_UNAVAILABLE"
    ERR_CONCURRENCY_LIMIT_EXCEEDED = "ERR_CONCURRENCY_LIMIT_EXCEEDED"
    ERR_LAYA_INFERENCE_TIMEOUT = "ERR_LAYA_INFERENCE_TIMEOUT"
    ERR_LLM_GENERATION_FAILED = "ERR_LLM_GENERATION_FAILED"

# Mapping from ErrorCode to default HTTP status code, title, and type URI
ERROR_METADATA: dict[ErrorCode, tuple[int, str, str]] = {
    ErrorCode.ERR_AUTH_ROLE_MISSING: (
        401,
        "Authentication Role Header Missing",
        "https://warden.enterprise/errors/auth-role-missing",
    ),
    ErrorCode.ERR_AUTH_ROLE_INVALID: (
        403,
        "Invalid Authentication Role",
        "https://warden.enterprise/errors/auth-role-invalid",
    ),
    ErrorCode.ERR_INGESTION_FILE_CORRUPT: (
        422,
        "Ingestion File Corrupt or Unparseable",
        "https://warden.enterprise/errors/ingestion-file-corrupt",
    ),
    ErrorCode.ERR_POISON_PILL_QUARANTINED: (
        422,
        "Document Quarantined to Dead-Letter Queue",
        "https://warden.enterprise/errors/poison-pill-quarantined",
    ),
    ErrorCode.ERR_QDRANT_UNAVAILABLE: (
        503,
        "Vector Datastore Unavailable",
        "https://warden.enterprise/errors/qdrant-unavailable",
    ),
    ErrorCode.ERR_CACHE_UNAVAILABLE: (
        503,
        "Distributed Cache Unavailable",
        "https://warden.enterprise/errors/cache-unavailable",
    ),
    ErrorCode.ERR_CONCURRENCY_LIMIT_EXCEEDED: (
        429,
        "Inference Concurrency Limit Exceeded",
        "https://warden.enterprise/errors/concurrency-limit-exceeded",
    ),
    ErrorCode.ERR_LAYA_INFERENCE_TIMEOUT: (
        504,
        "ModernBERT Decision Inference Timeout",
        "https://warden.enterprise/errors/laya-inference-timeout",
    ),
    ErrorCode.ERR_LLM_GENERATION_FAILED: (
        502,
        "Generative LLM Upstream Call Failed",
        "https://warden.enterprise/errors/llm-generation-failed",
    ),
}
