"""Data-access layer for release events.

All SQL lives here and nowhere else. The rest of the application talks to this
module via plain Python function calls and never builds queries directly.
Using SQLAlchemy's bound-parameter API means user-supplied values can never
be interpreted as SQL — injection is prevented by construction. To switch
storage backends (e.g. from SQLite to PostgreSQL or an external store), only
this file needs to change.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def fetch_by_id(db: Session, event_id: str) -> models.ReleaseEvent | None:
    """Load a single release event by primary key; return None if missing."""
    return db.get(models.ReleaseEvent, event_id)


def fetch_all(
    db: Session,
    *,
    service: str | None = None,
    status: models.EventStatus | None = None,
) -> list[models.ReleaseEvent]:
    """Query release events with optional filters.

    Filters combine with AND when more than one is supplied. Rows come back
    newest-first with the id as a tie-breaker, giving a stable ordering even
    when two events share the same timestamp.
    """
    predicates = []
    if service is not None:
        predicates.append(models.ReleaseEvent.service == service)
    if status is not None:
        predicates.append(models.ReleaseEvent.status == status)

    query = (
        select(models.ReleaseEvent)
        .where(*predicates)
        .order_by(models.ReleaseEvent.timestamp.desc(), models.ReleaseEvent.id)
    )
    return list(db.scalars(query).all())
