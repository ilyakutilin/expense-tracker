from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import db_settings


class PreBaseORM:
    repr_exclude_cols = ("created_at", "updated_at")

    def __repr__(self):
        """String representation of an ORM Model."""
        cols = []
        for col in self.__table__.columns.keys():  # type: ignore
            if col not in self.repr_exclude_cols:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} ({', '.join(cols)})>"


class BaseORM(AsyncAttrs, DeclarativeBase, PreBaseORM):
    pass


async_engine = create_async_engine(db_settings.db_url, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
