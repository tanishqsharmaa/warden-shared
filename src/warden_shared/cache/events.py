"""Cache Invalidation Event Models.

Denormalized from ARCHITECTURE_SPECIFICATION.md § 3.5.4.
"""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .keys import VALID_ROLE_TIERS


class CacheInvalidationEvent(BaseModel):
    """Event payload emitted by warden-ingestion upon successful batch indexing."""

    event: Literal["INGESTION_COMPLETED"] = Field(
        default="INGESTION_COMPLETED",
        description="Event classification identifier",
    )
    run_id: str = Field(
        ...,
        min_length=1,
        description="Unique batch execution run identifier",
    )
    affected_roles: list[str] = Field(
        ...,
        min_length=1,
        description="List of security role tiers affected by newly indexed documents",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO-8601 UTC timestamp of invalidation event",
    )

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("run_id cannot be empty or whitespace-only")
        return stripped

    @field_validator("affected_roles")
    @classmethod
    def validate_roles(cls, roles: list[str]) -> list[str]:
        for role in roles:
            if role not in VALID_ROLE_TIERS:
                raise ValueError(
                    f"Role '{role}' is invalid. Permitted roles: {sorted(VALID_ROLE_TIERS)}"
                )
        return roles
