"""Structured JSON Log Formatter with W3C Distributed Trace Correlation.

Denormalized from ARCHITECTURE_SPECIFICATION.md § 3.3.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from warden_shared.telemetry.tracer import get_current_trace_and_span_id

_RESERVED_LOG_ATTRS: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)

class WardenJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON with W3C trace correlation."""

    def __init__(
        self,
        service_name: str = "warden",
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.service_name = service_name
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format the specified record as a single-line JSON string."""
        trace_id, span_id = get_current_trace_and_span_id()
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": self.service_name,
            "trace_id": trace_id,
            "span_id": span_id,
            "message": record.getMessage(),
        }

        # Include default service-level extra fields
        for k, v in self.extra_fields.items():
            payload[k] = v

        # Extract custom fields attached via extra={...}
        for attr, value in record.__dict__.items():
            if attr not in _RESERVED_LOG_ATTRS and attr not in payload:
                payload[attr] = value

        # Exception information
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)

def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Configure standard stdout logging with WardenJSONFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to prevent duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(WardenJSONFormatter(service_name=service_name))
    root_logger.addHandler(handler)
