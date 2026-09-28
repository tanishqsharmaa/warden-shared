# warden-shared (Tier 0 Foundation Library)

Autonomous Enterprise Single Source of Truth (SSOT) — Shared Contracts & Distributed Primitives for Project Warden.

---

## 1. Overview
`warden-shared` is the foundational Python package (Tier 0 in the Project Warden build sequence) providing shared schemas, compiled Protocol Buffer v1 stubs, RFC 7807 problem details error hierarchies, OpenTelemetry distributed tracing helpers, and Redis RESP3/Sentinel connection pool utilities.

## 2. Core Modules

| Module | Purpose | Key Classes & Functions |
|---|---|---|
| `warden_shared.proto.v1` | Compiled Proto3 stubs for gRPC services | `retrieval_pb2`, `retrieval_pb2_grpc`, `laya_pb2`, `laya_pb2_grpc` |
| `warden_shared.errors` | RFC 7807 Problem Details & 9 enterprise errors | `ErrorCode`, `RFC7807ProblemDetails`, `WardenException`, `register_error_handlers` |
| `warden_shared.telemetry` | OpenTelemetry tracing & W3C propagation | `init_tracer`, `trace_span`, `inject_w3c_trace_context`, `extract_w3c_trace_context` |
| `warden_shared.cache` | Redis connection pool & cache key helpers | `RedisConnectionManager`, `format_query_cache_key`, `CacheInvalidationEvent` |
| `warden_shared.logging` | Structured single-line JSON logging with OTel | `WardenJSONFormatter`, `configure_logging` |

## 3. Installation

```bash
# Editable install in development
uv pip install -e .

# Or install wheel artifact
pip install Build/dist/warden_shared-1.0.0-py3-none-any.whl
```

## 4. Usage Examples

### 4.1 RFC 7807 Error Handling (FastAPI)
```python
from fastapi import FastAPI
from warden_shared.errors import register_error_handlers, RoleInvalidError

app = FastAPI()
register_error_handlers(app)

@app.get("/query")
async def query_endpoint():
    raise RoleInvalidError(detail="Role 'Contractor' is unauthorized.")
```

### 4.2 Distributed Tracing & W3C Propagation
```python
from warden_shared.telemetry import trace_span, inject_w3c_trace_context

@trace_span("retrieve_policies", attributes={"warden.caller_role": "Employee"})
async def execute_retrieval(query: str):
    headers = {}
    inject_w3c_trace_context(headers)
    # Forward headers over gRPC / HTTP
```

### 4.3 Deterministic Role-Scoped Cache Keys
```python
from warden_shared.cache import format_query_cache_key

# Automatically normalizes whitespace, unicode, and casing
cache_key = format_query_cache_key("Employee", "   How many PTO days?  \n")
# Returns: 'cache:query:Employee:64_char_sha256_hash'
```

### 4.4 Structured JSON Logging
```python
from warden_shared.logging import configure_logging
import logging

configure_logging(service_name="warden-retrieval", level="INFO")
logger = logging.getLogger("warden.retrieval")
logger.info("Hybrid search completed", extra={"candidates_count": 25})
```

## 5. Development & Testing

```bash
# Run complete test suite
pytest -v

# Run linting and type checking
ruff check src/ tests/
mypy --strict src/

# Recompile Protobuf schemas
python scripts/compile_protos.py
```
