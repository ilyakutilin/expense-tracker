from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseORM


class CRUDBase:
    def __init__(self, model: type[BaseORM]) -> None:
        self.model = model

    async def get_by_id(
        self, db_session: AsyncSession, obj_id: int, include_deleted: bool = False
    ) -> BaseORM | None:
        query = None
        if include_deleted:
            query = select(self.model).where(self.model.id_ == obj_id)
        else:
            query = select(self.model).where(
                and_(self.model.id_ == obj_id, self.model.is_active)
            )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, db_session: AsyncSession) -> list[BaseORM]:
        query = select(self.model).where(self.model.is_active)
        result = await db_session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db_session: AsyncSession,
        obj_data: dict[str, Any],
    ) -> BaseORM:
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
        obj_orm: BaseORM,
        obj_data: dict[str, Any],
    ) -> BaseORM:
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
        self, db_session: AsyncSession, obj_orm: BaseORM, perm: bool = False
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
