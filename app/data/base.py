"""Declarative base shared by all ORM models.

Kept in its own module so models can import ``Base`` without also pulling in
the engine, and so tooling like Alembic has a single, unambiguous import target
for autogenerate.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common base class for all SQLAlchemy ORM models."""
