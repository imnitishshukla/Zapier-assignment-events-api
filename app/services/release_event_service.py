"""Business logic layer for release events.

Sits between the HTTP routes and the data-access layer. Right now it mostly
passes calls through to the repository, but this is where domain logic should
live as requirements grow — things like computing per-service error rates,
flagging unusually long pipeline runs, or joining data from multiple sources.
Isolating this layer keeps routes thin and makes the storage layer replaceable
without touching any business rules.
"""

from sqlalchemy.orm import Session

from app import models, repositories


def fetch_by_id(db: Session, event_id: str) -> models.ReleaseEvent | None:
    """Look up one release event; returns None if the id is not found."""
    return repositories.fetch_by_id(db, event_id)


def fetch_all(
    db: Session,
    *,
    service: str | None = None,
    status: models.EventStatus | None = None,
) -> list[models.ReleaseEvent]:
    """Retrieve release events, optionally narrowed by service and/or status."""
    return repositories.fetch_all(
        db,
        service=service,
        status=status,
    )
