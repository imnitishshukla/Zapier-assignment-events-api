"""Structured error handling: domain exceptions and a consistent response shape.

Regardless of whether a request fails due to a missing resource, bad input,
or an unexpected crash, the API always returns the same JSON envelope so
clients never need to guess at the failure format:

    {
      "error": {
        "code": 404,
        "message": "Deployment not found",
        "status": "NOT_FOUND",
        "details": [ {"field": "service", "message": "..."} ]   # optional
      }
    }

``status`` is a stable UPPER_SNAKE string (Google API error style) that lets
clients branch on error type without coupling to numeric HTTP codes.
"""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.error")

# Starlette changed the name of the 422 constant between versions.
# Pick whichever one exists at import time so we stay compatible with both.
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None) or (
    status.HTTP_422_UNPROCESSABLE_ENTITY
)


# --------------------------------------------------------------------------- #
# Pydantic models (surface in the generated OpenAPI schema as well).
# --------------------------------------------------------------------------- #
class IssueDetail(BaseModel):
    """One field-level problem, used mainly inside validation error responses."""

    field: str | None = None
    message: str


class ErrorPayload(BaseModel):
    # HTTP status code, e.g. 404 — mirrors the response status line.
    code: int
    message: str
    # Machine-readable UPPER_SNAKE label, e.g. "NOT_FOUND".
    status: str
    details: list[IssueDetail] | None = None


class ErrorEnvelope(BaseModel):
    """Top-level wrapper present on every error response."""

    error: ErrorPayload


# --------------------------------------------------------------------------- #
# Domain exceptions — transport-agnostic.
# --------------------------------------------------------------------------- #
class AppError(Exception):
    """Base for all anticipated, client-facing error conditions."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    status_str: str = "INTERNAL"
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    status_str = "NOT_FOUND"
    message = "Resource not found"


# Legacy name aliases so older call sites continue to work without changes.
APIError = AppError
NotFoundError = ResourceNotFoundError


# --------------------------------------------------------------------------- #
# Response builder + per-exception handlers.
# --------------------------------------------------------------------------- #
def _build_error_body(
    code: int, message: str, status_str: str, details: list[dict] | None = None
) -> dict:
    body: dict = {"code": code, "message": message, "status": status_str}
    if details:
        body["details"] = details
    return {"error": body}


def _json_error_response(
    request: Request,
    status_code: int,
    message: str,
    status_str: str,
    details: list[dict] | None = None,
) -> JSONResponse:
    """Wrap the error payload in a JSONResponse and attach the trace id.

    Successful responses get the trace id from the middleware, but error
    responses can short-circuit that path, so the header is written here
    as well to guarantee it appears on every response.
    """
    resp = JSONResponse(
        status_code=status_code,
        content=_build_error_body(status_code, message, status_str, details),
    )
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        resp.headers["X-Request-ID"] = request_id
    return resp


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map a domain exception to the standard error envelope."""
    return _json_error_response(request, exc.status_code, exc.message, exc.status_str)


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Reformat Pydantic/FastAPI validation errors into the standard envelope."""
    details = []
    for err in exc.errors():
        # Drop the transport prefix ("body", "query", "path") from field paths.
        loc = [
            str(part)
            for part in err.get("loc", [])
            if part not in ("body", "query", "path")
        ]
        details.append(
            {"field": ".".join(loc) or None, "message": err.get("msg", "invalid")}
        )
    return _json_error_response(
        request,
        HTTP_422,
        "Request validation failed",
        "INVALID_ARGUMENT",
        details,
    )


async def starlette_http_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap Starlette-level HTTP errors (routing 404, 405, etc.) in the envelope."""
    status_str = {
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    }.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return _json_error_response(request, exc.status_code, message, status_str)


async def fallback_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler: log the full traceback, reply with a safe generic message.

    Nothing about the internal error is forwarded to the caller.
    """
    logger.exception(
        "unhandled exception on %s %s", request.method, request.url.path
    )
    return _json_error_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Internal server error",
        "INTERNAL",
    )


def attach_handlers(app) -> None:
    """Wire all exception handlers onto the FastAPI instance."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_handler)
    app.add_exception_handler(Exception, fallback_exception_handler)


# Legacy alias.
register_exception_handlers = attach_handlers
