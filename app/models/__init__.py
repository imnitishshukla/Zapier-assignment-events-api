"""ORM models — re-exported for convenient ``models.X`` access."""

from app.models.release_event_model import ReleaseEvent, EventStatus

# Backward-compatible aliases.
Deployment = ReleaseEvent
DeploymentStatus = EventStatus

__all__ = ["ReleaseEvent", "EventStatus", "Deployment", "DeploymentStatus"]
