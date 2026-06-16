"""Pytest fixtures shared across the test suite.

Each test case gets its own isolated in-memory SQLite database. The application
is wired to that database via ``build_application``, so tests never read or
write the real ``events.db`` file and cannot interfere with each other.
"""

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.base import Base
from app.main import build_application
from app.models.release_event_model import ReleaseEvent


@pytest.fixture()
def engine() -> Generator[Engine, None, None]:
    """Fresh in-memory SQLite engine, created and torn down per test."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine: Engine) -> sessionmaker:
    """Session factory bound to the test engine, used when inserting fixtures."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client(engine: Engine) -> Generator[TestClient, None, None]:
    # Bind the app to the test engine so the full startup path runs against
    # the in-memory DB with no globals to patch.
    application = build_application(engine=engine)
    with TestClient(application) as test_client:
        yield test_client


def create_test_event(**overrides) -> ReleaseEvent:
    """Construct a ReleaseEvent with sensible defaults; override any field as needed."""
    defaults = {
        "id": "evt_001",
        "service": "payment-service",
        "status": "failed",
        "duration": 275,
        "timestamp": datetime(2025, 5, 10, 9, 15, tzinfo=timezone.utc),
        "commit_sha": "f3a9c12b",
    }
    defaults.update(overrides)
    return ReleaseEvent(**defaults)


def insert_fixtures(session_factory: sessionmaker, events: list[ReleaseEvent]) -> None:
    """Persist a list of release events into the test database."""
    db = session_factory()
    try:
        db.add_all(events)
        db.commit()
    finally:
        db.close()


# Backward-compatible aliases for any tests still using the old names.
make_deployment = create_test_event
seed = insert_fixtures
