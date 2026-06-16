"""ORM table definition for pipeline release events.

Every row stores one service release — its result, how long the pipeline took,
and which commit kicked it off:

    {
      "id": "evt_abc123def456",
      "service": "payment-service",
      "status": "failed",
      "duration": 275,          # seconds
      "timestamp": "2025-05-10T09:15:00Z",
      "commit_sha": "f3a9c12"
    }
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.base import Base


class EventStatus(str, enum.Enum):
    """Possible outcomes for a pipeline release."""

    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    ROLLED_BACK = "rolled_back"


def _make_event_id() -> str:
    """Build a short, prefixed unique id (e.g. ``evt_3f1a9c2b4e7d``)."""
    return f"evt_{uuid.uuid4().hex[:12]}"


class ReleaseEvent(Base):
    """One pipeline run for a given service and commit."""

    __tablename__ = "release_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_make_event_id)
    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    # How many seconds the pipeline ran before reaching a terminal state.
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    # UTC timestamp of when this release was triggered.
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Joint index supports filtering by both service and status in one scan.
    __table_args__ = (Index("ix_release_service_status", "service", "status"),)
