"""Pydantic output schemas for the release events API.

These classes define exactly what the HTTP layer sends back to callers.
Keeping them separate from ORM models means the database schema can evolve
without breaking the published API contract.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.release_event_model import EventStatus


class ReleaseEventOut(BaseModel):
    """Wire representation of a single release event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    service: str
    status: EventStatus
    duration: int  # seconds
    timestamp: datetime
    commit_sha: str | None = None

    @field_serializer("timestamp", when_used="json")
    def _normalize_timestamp(self, value: datetime) -> str:
        """Always serialize timestamps as UTC ISO-8601 ending with ``Z``.

        SQLite does not preserve timezone info, so values read back from the
        database arrive as naive datetimes. Treat them as UTC and normalize
        before formatting so the API response is consistent regardless of which
        database backend is in use.

        Scoped to ``when_used="json"`` so in-process callers (e.g. tests using
        ``model_dump()``) still receive a real ``datetime`` object.
        """
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# Backward-compatible alias.
DeploymentOut = ReleaseEventOut
