"""Service layer — re-exported for convenient ``services.X`` access."""

from app.services.release_event_service import fetch_by_id, fetch_all

# Backward-compatible aliases.
get = fetch_by_id
list_deployments = fetch_all

__all__ = ["fetch_by_id", "fetch_all", "get", "list_deployments"]
