"""Top-level API router — aggregates all route modules."""

from fastapi import APIRouter

from app.api import release_event_routes

api_router = APIRouter()
api_router.include_router(release_event_routes.router)
