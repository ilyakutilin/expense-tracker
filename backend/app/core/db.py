from typing import AsyncGenerator

from sqlalchemy import BigInteger, Identity
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.core.settings import settings


class PreBaseORM:
    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower().replace("orm", "")  # type: ignore

    id_: Mapped[int] = mapped_column(
        "id",
        BigInteger,
        Identity(
            always=True,
            start=1,
            increment=1,
            nominvalue=True,
            nomaxvalue=True,
            cycle=False,
        ),
        primary_key=True,
        sort_order=-1,
    )

    def __repr__(self):
        """String representation of an ORM Model."""
        cols = []
        for col in self.__table__.columns.keys():  # type: ignore
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} ({', '.join(cols)})>"


class BaseORM(PreBaseORM, AsyncAttrs, DeclarativeBase):
    pass


async_engine = create_async_engine(settings.db_settings.db_url, echo=True, future=True)

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
