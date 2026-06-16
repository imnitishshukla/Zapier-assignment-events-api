"""Runtime configuration.

Every value that differs between environments is read from an environment
variable, so no deployment-specific data is ever committed to the repository.
Sensible defaults let the service start immediately for local development
with zero additional setup.
"""

import os


class AppConfig:
    """Typed access to environment-driven configuration values."""

    # Where SQLAlchemy should connect. Override via DATABASE_URL for any
    # database supported by SQLAlchemy (PostgreSQL, MySQL, etc.).
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./events.db")


app_config = AppConfig()

# Legacy alias so existing ``from app.core.config import settings`` still works.
settings = app_config
