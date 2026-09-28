"""Unit tests for cache invalidation event models."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from warden_shared.cache.events import CacheInvalidationEvent


def test_cache_invalidation_event_valid():
    now = datetime.now(timezone.utc)
    event = CacheInvalidationEvent(
        event="INGESTION_COMPLETED",
        run_id="ingest-run-7f93b5a1-432a-4a21-89e4-c5b55e34b921",
        affected_roles=["Employee", "Manager"],
        timestamp=now,
    )
    assert event.event == "INGESTION_COMPLETED"
    assert event.run_id == "ingest-run-7f93b5a1-432a-4a21-89e4-c5b55e34b921"
    assert event.affected_roles == ["Employee", "Manager"]
    assert event.timestamp == now

    data = event.model_dump(mode="json")
    assert data["event"] == "INGESTION_COMPLETED"
    assert data["affected_roles"] == ["Employee", "Manager"]
    assert "timestamp" in data

def test_cache_invalidation_event_invalid_role():
    with pytest.raises(ValidationError, match="Role 'Contractor' is invalid"):
        CacheInvalidationEvent(
            event="INGESTION_COMPLETED",
            run_id="ingest-run-001",
            affected_roles=["Contractor"],
        )

def test_cache_invalidation_event_empty_run_id():
    with pytest.raises(ValidationError):
        CacheInvalidationEvent(
            event="INGESTION_COMPLETED",
            run_id="",
            affected_roles=["Employee"],
        )

    with pytest.raises(ValidationError):
        CacheInvalidationEvent(
            event="INGESTION_COMPLETED",
            run_id="   ",
            affected_roles=["Employee"],
        )

def test_cache_invalidation_event_empty_roles():
    with pytest.raises(ValidationError):
        CacheInvalidationEvent(
            event="INGESTION_COMPLETED",
            run_id="ingest-run-001",
            affected_roles=[],
        )
