"""Repository layer — re-exported for convenient ``repositories.X`` access."""

from app.repositories.release_event_repository import fetch_by_id, fetch_all

# Backward-compatible aliases.
get = fetch_by_id
list_deployments = fetch_all

__all__ = ["fetch_by_id", "fetch_all", "get", "list_deployments"]
