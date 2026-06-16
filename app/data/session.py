"""Database engine, session factory, and request-scoped session dependency."""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import app_config

# ``check_same_thread=False`` is required by SQLite when connections are shared
# across threads (common in ASGI servers). The flag is ignored by other drivers
# so it is safe to apply conditionally.
_connect_args = (
    {"check_same_thread": False}
    if app_config.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(app_config.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(request: Request) -> Generator[Session, None, None]:
    """Open a database session for the current request, then close it on exit.

    Reads the session factory from ``app.state`` rather than a module global,
    which means each test can pass its own in-memory engine through
    ``build_application(engine=...)`` without any monkey-patching. Every
    request still gets its own short-lived session.
    """
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise RuntimeError(
            "session_factory missing from app.state — "
            "use build_application() to construct the app."
        )
    db = factory()
    try:
        yield db
    finally:
        db.close()
