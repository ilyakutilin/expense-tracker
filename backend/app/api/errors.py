from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException


def setup_exception_handlers(app: FastAPI):
    """Register all exception handlers"""

    # Handle our custom AppException
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        error_code = exc.error_code or type(exc).__name__
        request_id = getattr(request.state, "request_id", "unknown")
        lgr = logger.bind(request_id=request_id)
        log_func = lgr.error if exc.status_code >= 500 else lgr.debug
        log_msg = f"API Error: {error_code}"
        error_detail = {
            "code": error_code,
            "message": str(exc),
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        }

        log_func(log_msg, extra=error_detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {**error_detail, "request_id": request_id}},
        )

    # Handle FastAPI's validation errors
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handler for the request validation errors (user input)"""
        error_code = type(exc).__name__
        request_id = getattr(request.state, "request_id", "unknown")
        error_detail = {
            "code": error_code,
            "message": "Validation failed for one or several fields.",
            "detail": exc.errors(),
            "path": request.url.path,
            "method": request.method,
        }

        logger.bind(request_id=request_id).debug(
            "Request Validation Error", extra=error_detail
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": {**error_detail, "request_id": request_id}},
        )

    # Handle Pydantic validation errors
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handler for the internal validation errors."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.bind(request_id=request_id).error(
            "Internal Validation Error",
            extra={
                "code": "InternalValidationError",
                "message": str(exc),
                "detail": exc.errors(),
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected error occurred on the server side",
                    "detail": "Please contact support if this persists",
                    "path": request.url.path,
                    "request_id": request_id,
                }
            },
        )

    # Handle SQLAlchemy errors
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.bind(request_id=request_id).error(
            f"Database error: {exc}",
            extra={
                "code": "DatabaseError",
                "message": str(exc),
                "detail": {
                    "code": exc.code,
                },
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected error occurred on the server side",
                    "detail": "Please contact support if this persists",
                    "path": request.url.path,
                    "request_id": request_id,
                }
            },
        )

    # Handle all other exceptions (catch-all)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.bind(request_id=request_id).error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                "code": "UnhandledError",
                "message": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected error occurred on the server side",
                    "detail": "Please contact support if this persists",
                    "path": request.url.path,
                    "request_id": request_id,
                }
            },
        )
