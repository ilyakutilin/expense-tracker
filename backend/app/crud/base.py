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

    async def exist_multiple(
        self, db_session: AsyncSession, ids: list[int], include_deleted: bool = False
    ) -> list[int]:
        if not ids:
            return []

        stmt = select(self.model.id_).where(self.model.id_.in_(ids))

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)

        result = await db_session.execute(stmt)
        existing_ids = result.scalars().all()
        return list(existing_ids)

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
        self,
        db_session: AsyncSession,
        obj_data: dict[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        try:
            orm_obj = self.model(**obj_data)

            db_session.add(orm_obj)
            if commit:
                await db_session.commit()
            else:
                await db_session.flush()

            return orm_obj.id_

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def create_multiple(
        self,
        db_session: AsyncSession,
        data: list[dict[str, Any]],
        *,
        commit: bool = True,
    ) -> list[int]:
        try:
            orm_objs = [self.model(**item) for item in data]
            db_session.add_all(orm_objs)
            if commit:
                await db_session.commit()
            else:
                await db_session.flush()

            return [orm_obj.id_ for orm_obj in orm_objs]

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def update(
        self,
        db_session: AsyncSession,
        orm_obj: ModelType,
        data: dict[str, Any],
        *,
        commit: bool = True,
    ) -> int:
        for field, value in data.items():
            setattr(orm_obj, field, value)

        try:
            if commit:
                await db_session.commit()
            else:
                await db_session.flush()

            return orm_obj.id_

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

    async def commit(self, db_session: AsyncSession) -> None:
        try:
            await db_session.commit()
            db_session.expire_all()
        except SQLAlchemyError:
            await db_session.rollback()
            raise
