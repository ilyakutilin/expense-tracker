from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.errors import setup_exception_handlers
from app.api.middleware import I18nMiddleware, LoggingMiddleware, RequestIDMiddleware
from app.api.routers import main_router
from app.core.cache import cache
from app.core.logger import setup_logging
from app.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up FastAPI application")
    await cache.connect()

    yield

    logger.info("Shutting down FastAPI application")
    await cache.disconnect()
    logger.complete()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(I18nMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_exception_handlers(app)

    app.include_router(main_router)

    return app


app = create_application()
