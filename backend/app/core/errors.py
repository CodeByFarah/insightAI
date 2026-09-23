"""Application error types and the handlers that render them as JSON."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for errors that are safe to show to a user."""

    code = "INTERNAL_ERROR"
    status_code = 500
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: dict | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}

    def to_payload(self) -> dict:
        payload = {"error": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404
    message = "The requested resource does not exist."


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403
    message = "You do not have access to this resource."


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422
    message = "The request was not valid."


class InvalidFileError(AppError):
    code = "INVALID_FILE"
    status_code = 400
    message = "The uploaded file could not be accepted."


class FileTooLargeError(AppError):
    code = "FILE_TOO_LARGE"
    status_code = 413
    message = "The uploaded file exceeds the maximum allowed size."


class InvalidDatasetError(AppError):
    code = "INVALID_DATASET"
    status_code = 400
    message = "The uploaded CSV does not contain enough valid data for analysis."


class AnalysisNotFoundError(NotFoundError):
    code = "ANALYSIS_NOT_FOUND"
    message = "This dataset has not been analyzed yet."


class AIUnavailableError(AppError):
    code = "AI_UNAVAILABLE"
    status_code = 503
    message = (
        "AI analysis is currently unavailable. "
        "Your dataset analysis and visualizations are still available."
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every error leaves the API in the same shape."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Application error: %s", exc.message)
        else:
            logger.info("Handled error %s: %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "The request was not valid.",
                "details": {"fields": _summarise_validation(exc)},
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": _http_code(exc.status_code), "message": str(exc.detail)},
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Technical detail is logged; the client only ever sees a safe message.
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
            },
        )


def _summarise_validation(exc: RequestValidationError) -> list[dict]:
    return [
        {"field": ".".join(str(part) for part in error.get("loc", [])), "issue": error.get("msg", "")}
        for error in exc.errors()
    ]


def _http_code(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        413: "FILE_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        429: "RATE_LIMITED",
    }.get(status_code, "HTTP_ERROR")
