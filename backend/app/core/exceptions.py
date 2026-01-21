import pathlib
from typing import Any, Optional

from fastapi import status


class AppException(Exception):
    """Base exception for the application"""

    def __init__(
        self,
        status_code: int = 500,
        message: str = "Internal server error",
        detail: Any = None,
        error_code: Optional[str] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


# HTTP-related exceptions (4xx, 5xx)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, message=message, detail=detail
        )


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, message=message, detail=detail
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, message=message, detail=detail
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, message=message, detail=detail
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT, message=message, detail=detail
        )


class ReferentialIntergrityError(AppException):
    def __init__(
        self, message: str = "Referential integrity violation", detail: Any = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message=message,
            detail=detail,
        )


# class ValidationError(AppException):
#     def __init__(self, message: str = "Validation error", detail: Any = None):
#         super().__init__(
#             status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
#             message=message,
#             detail=detail,
#         )


# Business logic exceptions

# class BusinessRuleError(AppException):
#     def __init__(self, message: str = "Business rule violation", detail: Any = None):
#         super().__init__(
#             status_code=status.HTTP_400_BAD_REQUEST, message=message, detail=detail
#         )


# External service exceptions

# class ExternalServiceError(AppException):
#     def __init__(
#         self, service: str, message: str = "External service error", detail: Any = None
#     ):
#         super().__init__(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             message=f"{service}: {message}",
#             detail=detail,
#         )


# Database exceptions


class DatabaseError(AppException):
    def __init__(self, message: str = "Database error", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
        )


class CodeError(Exception):
    """Base exception for the errors that will not be displayed to API user."""

    pass


class PathError(CodeError):
    """Custom exception for path-related errors."""

    def __init__(self, path: str | pathlib.Path, message: str):
        self.path = str(path)
        self.message = message
        super().__init__(f"PathError for '{self.path}': {self.message}")


class CacheError(CodeError):
    """Exception for cache-related errors."""

    pass
