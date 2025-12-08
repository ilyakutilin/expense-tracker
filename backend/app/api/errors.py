from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppException


def setup_exception_handlers(app: FastAPI):
    """Register all exception handlers"""

    # Handle our custom AppException
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        error_code = exc.error_code or exc.__class__.__name__
        log_msg = f"API Error: {error_code}: {exc.message}"
        log_func = logger.error if exc.status_code >= 500 else logger.debug
        log_func(log_msg)
        error_detail = {
            "error": {
                "code": exc.error_code or exc.__class__.__name__,
                "message": exc.message,
                "detail": exc.detail,
                "path": request.url.path,
            }
        }
        return JSONResponse(status_code=exc.status_code, content=error_detail)

    # Handle FastAPI's validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = []
        messages = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
            messages.append(f"{error['loc'][-1]}: {error['msg']}")

        msg = f"Validation failed. {'; '.join(messages)}"
        code = "ValidationError"
        logger.debug(f"{code}. {msg}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": code,
                    "message": msg,
                    "detail": errors,
                    "path": request.url.path,
                }
            },
        )

    # Handle SQLAlchemy errors
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        # Log the full error for debugging
        logger.error(f"Database error: {exc}")

        if isinstance(exc, IntegrityError):
            error_detail = "Database integrity error"
            # Check for specific integrity errors
            if "duplicate key" in str(exc).lower():
                error_detail = "Duplicate entry"
        else:
            error_detail = "Database operation failed"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Database error occurred",
                    "detail": error_detail,
                    "path": request.url.path,
                }
            },
        )

    # Handle all other exceptions (catch-all)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log the full error
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "detail": "Please contact support if this persists",
                    "path": request.url.path,
                }
            },
        )
