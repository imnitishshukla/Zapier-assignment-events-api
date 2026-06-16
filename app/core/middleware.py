"""Request tracing middleware and structured access logging."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.requests")

TRACE_ID_HEADER = "X-Request-ID"


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Attach a trace id to every request and log one line when it completes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept a trace id forwarded by an upstream gateway, or mint a fresh one.
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = trace_id

        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request failed",
                extra={
                    "request_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": elapsed_ms,
                },
            )
            raise

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers[TRACE_ID_HEADER] = trace_id
        logger.info(
            "request completed",
            extra={
                "request_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
            },
        )
        return response


# Legacy alias.
RequestContextMiddleware = TraceContextMiddleware
