from typing import Any, Generic, TypeVar

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.models.base import BaseORM

ModelType = TypeVar("ModelType", bound="BaseORM")


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    @classmethod
    def _get_options(cls) -> tuple[_AbstractLoad, ...]:
        return tuple()

    async def exists(
        self, db_session: AsyncSession, include_deleted: bool = False, **params
    ) -> bool:
        stmt = select(self.model.id_)

        for attr, value in params.items():
            if not hasattr(self.model, attr):
                raise AttributeError(f"{self.model.__name__} has no attribute '{attr}'")
            stmt = stmt.where(getattr(self.model, attr) == value)

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
        result = await db_session.scalar(stmt)
        return result is not None

    async def get_by_id(
        self, db_session: AsyncSession, obj_id: int, include_deleted: bool = False
    ) -> ModelType | None:
        stmt = select(self.model).where(self.model.id_ == obj_id)
        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
        stmt = stmt.options(*self._get_options())
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(
        self, db_session: AsyncSession, include_deleted: bool = False, **params
    ) -> ModelType | None:
        stmt = select(self.model)

        for attr, value in params.items():
            if not hasattr(self.model, attr):
                raise AttributeError(f"{self.model.__name__} has no attribute '{attr}'")
            stmt = stmt.where(getattr(self.model, attr) == value)

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)

        stmt = stmt.options(*self._get_options())
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db_session: AsyncSession,
        include_deleted: bool = False,
        filter_: Filter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ModelType], int]:
        stmt = select(self.model)

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)

        if filter_:
            stmt = filter_.filter(stmt)
            stmt = filter_.sort(stmt)

        stmt = stmt.options(*self._get_options())

        total: int | None = None
        offset = (page - 1) * page_size

        count_query = select(func.count()).select_from(self.model)
        total_result = await db_session.execute(count_query)
        total = total_result.scalar_one()

        stmt = stmt.offset(offset).limit(page_size)

        result = await db_session.execute(stmt)
        accounts = list(result.scalars().all())

        return accounts, total

    async def create(
        self, db_session: AsyncSession, obj_data: dict[str, Any], refresh: bool = True
    ) -> ModelType:
        try:
            obj_orm = self.model(**obj_data)

            db_session.add(obj_orm)
            await db_session.commit()

            if refresh:
                await db_session.refresh(obj_orm)

            return obj_orm

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def update(
        self,
        db_session: AsyncSession,
        obj_orm: ModelType,
        obj_data: dict[str, Any],
    ) -> ModelType:
        for field, value in obj_data.items():
            setattr(obj_orm, field, value)

        try:
            db_session.add(obj_orm)
            await db_session.commit()
            await db_session.refresh(obj_orm)

            return obj_orm

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def delete(
        self, db_session: AsyncSession, obj_orm: ModelType, perm: bool = False
    ) -> None:
        try:
            if perm:
                await db_session.delete(obj_orm)
            else:
                obj_orm.is_deleted = True
            await db_session.commit()

        except SQLAlchemyError:
            await db_session.rollback()
            raise
