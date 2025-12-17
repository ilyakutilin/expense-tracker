from typing import Any, Generic, TypeVar

from sqlalchemy import select
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
        self, db_session: AsyncSession, obj_id: int, include_deleted: bool = False
    ) -> bool:
        stmt = select(self.model.id_).where(self.model.id_ == obj_id)
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

    async def get_all(self, db_session: AsyncSession) -> list[ModelType]:
        stmt = select(self.model).where(self.model.is_active)
        stmt = stmt.options(*self._get_options())
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        db_session: AsyncSession,
        obj_data: dict[str, Any],
    ) -> ModelType:
        try:
            obj_orm = self.model(**obj_data)

            db_session.add(obj_orm)
            await db_session.commit()
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
