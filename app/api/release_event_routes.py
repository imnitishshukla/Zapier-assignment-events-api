"""HTTP endpoints for querying pipeline release events."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.core.errors import ErrorEnvelope, ResourceNotFoundError
from app.data.session import get_db

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get(
    "",
    response_model=list[schemas.ReleaseEventOut],
    summary="List release events (optionally filtered by service and/or status)",
)
def list_events(
    response: Response,
    db: Session = Depends(get_db),
    service: str | None = Query(default=None, max_length=100, description="Exact service name"),
    status: models.EventStatus | None = Query(
        default=None, description="Filter by event status"
    ),
) -> list[models.ReleaseEvent]:
    results = services.fetch_all(
        db,
        service=service,
        status=status,
    )
    # Carry the total match count in a header; the body stays a flat list.
    response.headers["X-Total-Count"] = str(len(results))
    return results


@router.get(
    "/{event_id}",
    response_model=schemas.ReleaseEventOut,
    responses={404: {"model": ErrorEnvelope, "description": "Event not found"}},
    summary="Retrieve a single release event by id",
)
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
) -> models.ReleaseEvent:
    event = services.fetch_by_id(db, event_id)
    if event is None:
        raise ResourceNotFoundError("Deployment not found")
    return event
