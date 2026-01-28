import pathlib
from typing import Any

from fastapi import status

from app.core.i18n import TranslatableMessage, _, translate


class AppException(Exception):
    """Base exception for the application"""

    def __init__(
        self,
        status_code: int = 500,
        translatable_message: TranslatableMessage | None = None,
        fallback_message: str | None = None,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.message = fallback_message or "Internal Server Error"
        if translatable_message is not None and translatable_message.is_valid():
            self.message = translate(translatable_message)
        self.detail = detail
        self.headers = headers
        self.error_code = self.__class__.__name__

        super().__init__(self.message)


# HTTP-related exceptions (4xx, 5xx)


class NotFoundError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _("Resource not found"),
        detail: Any = None,
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            translatable_message=translatable_message,
            fallback_message="Resource not found",
            detail=detail,
        )


class BadRequestError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _("Bad request"),
        detail: Any = None,
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            translatable_message=translatable_message,
            fallback_message="Bad request",
            detail=detail,
        )


class UnauthorizedError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _("Unauthorized"),
        detail: Any = None,
        headers: dict[str, str] = {"WWW-Authenticate": "Bearer"},
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            translatable_message=translatable_message,
            fallback_message="Unauthorized",
            detail=detail,
            headers=headers,
        )


class ForbiddenError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _("Forbidden"),
        detail: Any = None,
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            translatable_message=translatable_message,
            fallback_message="Forbidden",
            detail=detail,
        )


class ConflictError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _("Conflict"),
        detail: Any = None,
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            translatable_message=translatable_message,
            fallback_message="Conflict",
            detail=detail,
        )


class ReferentialIntergrityError(AppException):
    def __init__(
        self,
        translatable_message: TranslatableMessage = _(
            "Referential integrity violation"
        ),
        detail: Any = None,
        **msg_kwargs,
    ):
        translatable_message.kwargs = msg_kwargs
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            translatable_message=translatable_message,
            fallback_message="Referential integrity violation",
            detail=detail,
        )


# Database exceptions


class DatabaseError(AppException):
    def __init__(self, message: str = "Database error", detail: Any = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            fallback_message=message,
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
