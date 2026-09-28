"""Unit tests for structured JSON logger with W3C trace correlation."""
import json
import logging
import sys

from warden_shared.logging.json_logger import WardenJSONFormatter, configure_logging
from warden_shared.telemetry.tracer import init_tracer, trace_span


def test_json_formatter_without_active_otel_span():
    formatter = WardenJSONFormatter(service_name="warden-retrieval")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="retrieval.py",
        lineno=42,
        msg="Hybrid retrieval completed",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["service"] == "warden-retrieval"
    assert data["level"] == "INFO"
    assert data["message"] == "Hybrid retrieval completed"
    assert data["trace_id"] == ""
    assert data["span_id"] == ""
    assert "timestamp" in data

def test_json_formatter_with_active_otel_span():
    init_tracer("warden-test-logger")
    formatter = WardenJSONFormatter(service_name="warden-retrieval")

    with trace_span("execute_query_span"):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="retrieval.py",
            lineno=42,
            msg="Inside active trace",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert len(data["trace_id"]) == 32
        assert len(data["span_id"]) == 16
        assert data["service"] == "warden-retrieval"

def test_json_formatter_with_exception():
    formatter = WardenJSONFormatter(service_name="warden-retrieval")
    try:
        raise ValueError("Database connection lost")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="retrieval.py",
        lineno=50,
        msg="Error during query",
        args=(),
        exc_info=exc_info,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "ERROR"
    assert "exception" in data
    assert "Database connection lost" in data["exception"]

def test_json_formatter_extra_attributes():
    formatter = WardenJSONFormatter(
        service_name="warden-retrieval",
        extra_fields={"environment": "production"},
    )
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="retrieval.py",
        lineno=60,
        msg="Retrieval event",
        args=(),
        exc_info=None,
    )
    record.caller_role = "Employee"  # type: ignore[attr-defined]
    record.candidates_count = 25  # type: ignore[attr-defined]

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["environment"] == "production"
    assert data["caller_role"] == "Employee"
    assert data["candidates_count"] == 25

def test_configure_logging():
    configure_logging(service_name="warden-orchestrator", level="DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, WardenJSONFormatter)
    assert root_logger.handlers[0].formatter.service_name == "warden-orchestrator"

def test_json_formatter_z_timestamp_and_taskname_suppression():
    formatter = WardenJSONFormatter(service_name="warden-retrieval")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="retrieval.py",
        lineno=70,
        msg="Check timestamp and taskName",
        args=(),
        exc_info=None,
    )
    record.taskName = "Task-42"  # type: ignore[attr-defined]
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["timestamp"].endswith("Z")
    assert "+00:00" not in data["timestamp"]
    assert "taskName" not in data

