from typing import Any, Sequence, TypeGuard

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from app.core.i18n import _

PYDANTIC_VALIDATION_ERROR_MESSAGES = {
    "arguments_type": _("Arguments must be a tuple, list or a dictionary"),
    "assertion_error": _("Assertion failed, {error}"),
    "bool_parsing": _("Input should be a valid boolean, unable to interpret input"),
    "bool_type": _("Input should be a valid boolean"),
    "bytes_invalid_encoding": _("Data should be valid {encoding}: {encoding_error}"),
    "bytes_too_long": _("Data should have at most {max_length} byte{expected_plural}"),
    "bytes_too_short": _(
        "Data should have at least {min_length} byte{expected_plural}"
    ),
    "bytes_type": _("Input should be a valid bytes"),
    "callable_type": _("Input should be callable"),
    "complex_str_parsing": _(
        "Input should be a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex"
    ),
    "complex_type": _(
        "Input should be a valid python complex object, a number, or a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex"
    ),
    "dataclass_exact_type": _("Input should be an instance of {class_name}"),
    "dataclass_type": _("Input should be a dictionary or an instance of {class_name}"),
    "date_from_datetime_inexact": _(
        "Datetimes provided to dates should have zero time - e.g. be exact dates"
    ),
    "date_from_datetime_parsing": _(
        "Input should be a valid date or datetime, {error}"
    ),
    "date_future": _("Date should be in the future"),
    "date_parsing": _("Input should be a valid date in the format YYYY-MM-DD, {error}"),
    "date_past": _("Date should be in the past"),
    "date_type": _("Input should be a valid date"),
    "datetime_from_date_parsing": _(
        "Input should be a valid datetime or date, {error}"
    ),
    "datetime_future": _("Input should be in the future"),
    "datetime_object_invalid": _("Invalid datetime object, got {error}"),
    "datetime_parsing": _("Input should be a valid datetime, {error}"),
    "datetime_past": _("Input should be in the past"),
    "datetime_type": _("Input should be a valid datetime"),
    "decimal_max_digits": _(
        "Decimal input should have no more than {max_digits} digit{expected_plural} in total"
    ),
    "decimal_max_places": _(
        "Decimal input should have no more than {decimal_places} decimal place{expected_plural}"
    ),
    "decimal_parsing": _("Input should be a valid decimal"),
    "decimal_type": _(
        "Decimal input should be an integer, float, string or Decimal object"
    ),
    "decimal_whole_digits": _(
        "Decimal input should have no more than {whole_digits} digit{expected_plural} before the decimal point"
    ),
    "default_factory_not_called": _(
        "The default factory uses validated data, but at least one validation error occurred"
    ),
    "dict_type": _("Input should be a valid dictionary"),
    "enum": _("Input should be {expected}"),
    "extra_forbidden": _("Extra inputs are not permitted"),
    "finite_number": _("Input should be a finite number"),
    "float_parsing": _(
        "Input should be a valid number, unable to parse string as a number"
    ),
    "float_type": _("Input should be a valid number"),
    "frozen_field": _("Field is frozen"),
    "frozen_instance": _("Instance is frozen"),
    "frozen_set_type": _("Input should be a valid frozenset"),
    "get_attribute_error": _("Error extracting attribute: {error}"),
    "greater_than": _("Input should be greater than {gt}"),
    "greater_than_equal": _("Input should be greater than or equal to {ge}"),
    "int_from_float": _(
        "Input should be a valid integer, got a number with a fractional part"
    ),
    "int_parsing": _(
        "Input should be a valid integer, unable to parse string as an integer"
    ),
    "int_parsing_size": _(
        "Unable to parse input string as an integer, exceeded maximum size"
    ),
    "int_type": _("Input should be a valid integer"),
    "invalid_key": _("Keys should be strings"),
    "is_instance_of": _("Input should be an instance of {class}"),
    "is_subclass_of": _("Input should be a subclass of {class}"),
    "iterable_type": _("Input should be iterable"),
    "iteration_error": _("Error iterating over object, error: {error}"),
    "json_invalid": _("Invalid JSON: {error}"),
    "json_type": _("JSON input should be string, bytes or bytearray"),
    "less_than": _("Input should be less than {lt}"),
    "less_than_equal": _("Input should be less than or equal to {le}"),
    "list_type": _("Input should be a valid list"),
    "literal_error": _("Input should be {expected}"),
    "mapping_type": _("Input should be a valid mapping, error: {error}"),
    "missing": _("Field required"),
    "missing_argument": _("Missing required argument"),
    "missing_keyword_only_argument": _("Missing required keyword only argument"),
    "missing_positional_only_argument": _("Missing required positional only argument"),
    "missing_sentinel_error": _("Input should be the 'MISSING' sentinel"),
    "model_attributes_type": _(
        "Input should be a valid dictionary or object to extract fields from"
    ),
    "model_type": _("Input should be a valid dictionary or instance of {class_name}"),
    "multiple_argument_values": _("Got multiple values for argument"),
    "multiple_of": _("Input should be a multiple of {multiple_of}"),
    "needs_python_object": _(
        "Cannot check `{method_name}` when validating from json, use a JsonOrPython validator instead"
    ),
    "no_such_attribute": _("Object has no attribute '{attribute}'"),
    "none_required": _("Input should be None"),
    "recursion_loop": _("Recursion error - cyclic reference detected"),
    "set_item_not_hashable": _("Set items should be hashable"),
    "set_type": _("Input should be a valid set"),
    "string_pattern_mismatch": _("String should match pattern '{pattern}'"),
    "string_sub_type": _(
        "Input should be a string, not an instance of a subclass of str"
    ),
    "string_too_long": _(
        "String should have at most {max_length} character{expected_plural}"
    ),
    "string_too_short": _(
        "String should have at least {min_length} character{expected_plural}"
    ),
    "string_type": _("Input should be a valid string"),
    "string_unicode": _(
        "Input should be a valid string, unable to parse raw data as a unicode string"
    ),
    "time_delta_parsing": _("Input should be a valid timedelta, {error}"),
    "time_delta_type": _("Input should be a valid timedelta"),
    "time_parsing": _("Input should be in a valid time format, {error}"),
    "time_type": _("Input should be a valid time"),
    "timezone_aware": _("Input should have timezone info"),
    "timezone_naive": _("Input should not have timezone info"),
    "too_long": _(
        "{field_type} should have at most {max_length} item{expected_plural} after validation, not {actual_length}"
    ),
    "too_short": _(
        "{field_type} should have at least {min_length} item{expected_plural} after validation, not {actual_length}"
    ),
    "tuple_type": _("Input should be a valid tuple"),
    "unexpected_keyword_argument": _("Unexpected keyword argument"),
    "unexpected_positional_argument": _("Unexpected positional argument"),
    "union_tag_invalid": _(
        "Input tag '{tag}' found using {discriminator} does not match any of the expected tags: {expected_tags}"
    ),
    "union_tag_not_found": _(
        "Unable to extract tag using discriminator {discriminator}"
    ),
    "url_parsing": _("Input should be a valid URL, {error}"),
    "url_scheme": _("URL scheme should be {expected_schemes}"),
    "url_syntax_violation": _("Input violated strict URL syntax rules, {error}"),
    "url_too_long": _(
        "URL should have at most {max_length} character{expected_plural}"
    ),
    "url_type": _("URL input should be a string or URL"),
    "uuid_parsing": _("Input should be a valid UUID, {error}"),
    "uuid_type": _("UUID input should be a string, bytes or UUID object"),
    "uuid_version": _("UUID version {expected_version} expected"),
    "value_error": _("Value error, {error}"),
}


def _parse_pydantic_error_msg(error: ErrorDetails) -> str:
    """
    Parse a Pydantic error using its type and context.
    """
    error_type = error["type"]
    ctx = error.get("ctx", {})

    # Get the translatable message template
    message_template = PYDANTIC_VALIDATION_ERROR_MESSAGES.get(
        error_type, error.get("msg", "Validation error")
    )

    # Apply context values if present
    message = message_template
    if ctx:
        try:
            message = message_template.format(**ctx)
        except KeyError:
            # If some placeholders are missing, fall back to original
            pass

    return message


def _is_error_details(obj: Any) -> TypeGuard[ErrorDetails]:
    """Type guard for ErrorDetails."""
    if not isinstance(obj, dict):
        return False

    required_keys = {"type", "loc", "msg", "input"}
    if not required_keys.issubset(obj.keys()):
        return False

    return (
        isinstance(obj.get("type"), str)
        and isinstance(obj.get("loc"), tuple)
        and isinstance(obj.get("msg"), str)
    )


def _parse_validation_error_details(errors: Sequence[Any]) -> list[dict[str, str]]:
    translated_errors = []

    for err in errors:
        if _is_error_details(err):
            translated_errors.append(
                {
                    "type": err.get("type", ""),
                    "loc": ".".join([str(item) for item in err.get("loc", tuple())]),
                    "msg": _parse_pydantic_error_msg(err),
                }
            )

    return translated_errors


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
            "detail": _parse_validation_error_details(exc.errors()),
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
                "detail": _parse_validation_error_details(exc.errors()),
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
