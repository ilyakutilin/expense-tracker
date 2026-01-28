import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.i18n import set_locale
from app.utils.idgen import generate_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = generate_request_id()
        request.state.request_id = request_id

        with logger.contextualize(request_id=request_id):
            response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()

        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        logger.bind(request_id=request_id).info(
            f"Request started: {method} {url} from {client_host}"
        )

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            logger.bind(request_id=request_id).info(
                f"Request completed: {method} {url}",
                extra={
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                },
            )
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.bind(request_id=request_id).error(
                f"Request failed: {method} {url}",
                extra={
                    "status_code": response.status_code,
                    "error": str(e),
                    "process_time": f"{process_time:.3f}s",
                },
            )
            raise


class I18nMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, supported_locales=None):
        super().__init__(app)
        self.supported_locales = supported_locales or ["en", "ru"]

    async def dispatch(self, request: Request, call_next):
        # Parse Accept-Language header
        locale = self.get_locale_from_header(request)
        set_locale(locale)

        response = await call_next(request)
        return response

    def get_locale_from_header(self, request: Request) -> str:
        """Extract locale from Accept-Language header"""
        accept_language = request.headers.get("Accept-Language", "en")

        # Parse the Accept-Language header (simplified)
        # Format: "en-US,en;q=0.9,es;q=0.8"
        for lang in accept_language.split(","):
            lang_code = lang.split(";")[0].strip().split("-")[0]
            if lang_code in self.supported_locales:
                return lang_code

        # Default to English
        return "en"
