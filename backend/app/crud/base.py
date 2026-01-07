from typing import Any, Generic, TypeVar

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import _AbstractLoad

from app.filters.base import FilterConditions
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
        filter_conditions: FilterConditions,
        include_deleted: bool = False,
        unique: bool = False,
    ) -> tuple[list[ModelType], int]:
        stmt = select(self.model)
        count_stmt = select(func.count(self.model.id_))

        if not include_deleted:
            stmt = stmt.where(self.model.is_active)
            count_stmt = count_stmt.where(self.model.is_active)

        if filter_conditions.has_filters():
            for condition in filter_conditions.where_clauses:
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

        total_count_result = await db_session.execute(count_stmt)
        total_count = total_count_result.scalar_one()

        stmt = stmt.options(*self._get_options())

        if filter_conditions.has_ordering():
            for order_clause in filter_conditions.order_by_clauses:
                stmt = stmt.order_by(order_clause)

        if filter_conditions.has_pagination():
            offset, limit = filter_conditions.offset_limit
            stmt = stmt.offset(offset).limit(limit)

        stmt = stmt.options(*self._get_options())

        result = await db_session.execute(stmt)
        scalar_result: ScalarResult[ModelType] = result.scalars()
        if unique:
            scalar_result = scalar_result.unique()
        orm_objs = list(scalar_result.all())

        return orm_objs, total_count

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
    ) -> int | None:
        for field, value in data.items():
            setattr(orm_obj, field, value)

        is_modified: bool = db_session.is_modified(orm_obj)

        try:
            if commit:
                await db_session.commit()
            else:
                await db_session.flush()

            return orm_obj.id_ if is_modified else None

        except SQLAlchemyError:
            await db_session.rollback()
            raise

    async def mark_updated(
        self,
        db_session: AsyncSession,
        orm_obj: ModelType,
        *,
        commit: bool = True,
    ) -> int:
        orm_obj.updated_at = func.now()

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
        # TODO: Maybe just ID instead of ORM object?
        self,
        db_session: AsyncSession,
        obj_orm: ModelType,
        perm: bool = False,
    ) -> None:
        try:
            if perm:
                await db_session.delete(obj_orm)
            else:
                obj_orm.is_deleted = True
                obj_orm.deleted_at = func.now()
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
