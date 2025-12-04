import time

from fastapi import Request
from loguru import logger


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    method = request.method
    url = str(request.url)
    client_host = request.client.host if request.client else "unknown"

    logger.info(f"Request started: {method} {url} from {client_host}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"Request completed: {method} {url} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {method} {url} "
            f"Error: {str(e)} "
            f"Duration: {process_time:.3f}s"
        )
        raise


# Add it to your app like this:
# app.middleware("http")(logging_middleware)
