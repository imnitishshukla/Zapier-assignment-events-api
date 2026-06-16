"""Application factory for the Release Events API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app import __version__, models  # noqa: F401  (registers ORM tables with SQLAlchemy)
from app.core.errors import attach_handlers
from app.core.logging import init_logging
from app.core.middleware import TraceContextMiddleware
from app.data.base import Base
from app.data import session as db_session
from app.api.router import api_router

# Set up JSON logging before any other code runs.
init_logging()


def build_application(engine: Engine | None = None) -> FastAPI:
    """Assemble and return a fully configured FastAPI application.

    Passing a custom ``engine`` lets tests inject an isolated in-memory
    database without touching module-level globals. The engine and matching
    session factory are stored on ``app.state`` so every request resolves
    them through ``get_db`` rather than a shared global.
    """
    if engine is None:
        engine = db_session.engine
        session_factory = db_session.SessionLocal
    else:
        session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Run schema creation at startup rather than at import time.

        This avoids database side-effects when the module is imported (e.g.
        during test collection). A real production deployment would handle
        migrations via Alembic instead.
        """
        Base.metadata.create_all(bind=app.state.engine)
        yield

    application = FastAPI(
        title="Release Events API",
        version=__version__,
        description=(
            "Backend service for recording and querying pipeline release event history."
        ),
        lifespan=lifespan,
    )
    application.state.engine = engine
    application.state.session_factory = session_factory

    application.add_middleware(TraceContextMiddleware)
    attach_handlers(application)
    application.include_router(api_router)

    return application


# Default instance picked up by uvicorn and other ASGI runners.
app = build_application()

# Legacy alias.
create_app = build_application
