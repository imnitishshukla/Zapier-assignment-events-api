"""JSON log formatter and root-logger setup.

Each log record is written as a single JSON line so log aggregators can parse
and index fields without regex heuristics. Per-request context (trace id,
method, path, status, latency) is injected by the middleware and picked up
here automatically. Credentials and request bodies are never included.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class StructuredLogFormatter(logging.Formatter):
    """Serialize a log record to a compact JSON string."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Pull in any request-scoped extras set by the middleware logger.
        for key in ("request_id", "method", "path", "status_code", "latency_ms"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def init_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger. Calling it twice is harmless."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredLogFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


# Legacy alias.
configure_logging = init_logging
