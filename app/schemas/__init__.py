"""Pydantic schemas — re-exported for convenient ``schemas.X`` access."""

from app.schemas.release_event_schemas import ReleaseEventOut

# Backward-compatible alias.
DeploymentOut = ReleaseEventOut

__all__ = ["ReleaseEventOut", "DeploymentOut"]
