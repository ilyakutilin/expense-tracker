from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings

async_engine = create_async_engine(settings.db_settings.db_url, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created")
            yield session
        except Exception as e:
            await session.rollback()
            logger.debug(f"Database session rolled back: {e}")
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")
