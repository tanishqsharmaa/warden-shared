"""FastAPI Exception Handlers for RFC 7807 Problem Details."""
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import WardenException
from .problem_details import RFC7807ProblemDetails

logger = logging.getLogger("warden.errors")


def register_error_handlers(app: FastAPI) -> None:
    """Register RFC 7807 Problem Details exception handlers on a FastAPI instance."""

    @app.exception_handler(WardenException)
    async def warden_exception_handler(request: Request, exc: WardenException) -> JSONResponse:
        pd = exc.to_problem_details(instance=request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content=pd.model_dump(mode="json", exclude_none=True),
            media_type="application/problem+json",
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception processing %s: %s", request.url.path, exc)
        pd = RFC7807ProblemDetails(
            type="https://warden.enterprise/errors/internal-server-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected internal server error occurred.",
            instance=request.url.path,
            error_code=str(getattr(exc, "error_code", "ERR_INTERNAL_SERVER_ERROR")),
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(
            status_code=500,
            content=pd.model_dump(mode="json", exclude_none=True),
            media_type="application/problem+json",
        )
