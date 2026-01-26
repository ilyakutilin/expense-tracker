import math
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core import exceptions as exc
from app.core.auth.security import get_password_hash
from app.core.cache import cached, invalidate_cache
from app.core.i18n import _
from app.crud import CRUDUser, user_crud
from app.filters.user import UserFilterParams
from app.models.user import UserORM
from app.schemas.cache import CachePattern, Entity
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserCreate, UserResponseAdmin, UserUpdate
from app.services import get_msg

DETAIL_PATTERN = CachePattern(
    entity=Entity.USER,
    obj_id_key="user_id",
    is_user_owned=False,
)

LIST_PATTERN = CachePattern(
    entity=Entity.USER,
    obj_id_key=None,
    is_user_owned=False,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: CRUDUser = user_crud

    async def _get_user_orm_by_id(
        self, user_id: int, include_deleted: bool = False
    ) -> UserORM:
        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db,
            obj_id=user_id,
            include_deleted=include_deleted,
        )
        if not user_orm:
            raise exc.NotFoundError(
                message=get_msg(_("User with id {user_id} not found"), user_id=user_id),
                detail={"id": user_id},
            )
        return user_orm

    async def _check_email_exists(self, email: str) -> None:
        exists: bool = await self.crud.exists(self.db, email=email)
        if exists:
            raise exc.ConflictError(
                message=get_msg(
                    _("User with email '{email}' already exists"), email=email
                ),
                detail={"email": email},
            )

    @cached(pattern=DETAIL_PATTERN, response_model=UserResponseAdmin)
    async def get_user_by_id(
        self, *, user_id: int, include_deleted: bool = False
    ) -> UserResponseAdmin:
        user_orm: UserORM = await self._get_user_orm_by_id(user_id, include_deleted)
        return UserResponseAdmin.model_validate(user_orm)

    @cached(pattern=LIST_PATTERN, response_model=PaginatedResponse[UserResponseAdmin])
    async def get_all_users(
        self,
        *,
        filter_params: UserFilterParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[UserResponseAdmin]:
        conditions = filter_params.manager.build_conditions(filter_params)

        user_orms, total_count = await self.crud.get_all(
            db_session=self.db,
            filter_conditions=conditions,
            include_deleted=include_deleted,
            unique=True,
        )
        users = [UserResponseAdmin.model_validate(t) for t in user_orms]

        if total_count is None:
            raise exc.CodeError("Total count of users cannot be None")

        return PaginatedResponse[UserResponseAdmin](
            total=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=math.ceil(total_count / filter_params.page_size)
            if total_count > 0
            else 0,
            items=users,
        )

    @invalidate_cache(LIST_PATTERN)
    async def create_user(self, *, user_create: UserCreate) -> UserResponseAdmin:
        await self._check_email_exists(user_create.email)
        user_data: dict[str, Any] = user_create.model_dump()
        hashed_password = get_password_hash(str(user_create.password))
        user_data["password_hash"] = hashed_password
        user_id: int = await self.crud.create(self.db, obj_data=user_data, commit=True)
        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db, obj_id=user_id, include_deleted=False
        )
        if not user_orm:
            raise exc.DatabaseError(
                message=(_("Created user could not be fetched from the database")),
                detail={"id": user_id, "email": user_create.email},
            )
        return UserResponseAdmin.model_validate(user_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def update_user(
        self, *, user_id: int, user_update: UserUpdate
    ) -> UserResponseAdmin:
        user_orm: UserORM = await self._get_user_orm_by_id(user_id)

        if user_update.email:
            await self._check_email_exists(user_update.email)

        user_data: dict[str, Any] = user_update.model_dump(exclude_unset=True)

        if user_update.password:
            hashed_password = get_password_hash(str(user_update.password))
            user_data["password_hash"] = hashed_password

        user_data: dict[str, Any] = user_update.model_dump(exclude_unset=True)
        if not user_data:
            raise exc.BadRequestError(
                message=_("No fields to update"), detail={"id": user_id}
            )

        updated_user_id: int | None = await self.crud.update(
            db_session=self.db, orm_obj=user_orm, data=user_data, commit=True
        )
        updated_user_orm: UserORM | None = None
        if updated_user_id:
            updated_user_orm: UserORM | None = await self.crud.get_by_id(
                self.db, obj_id=updated_user_id
            )
            if not updated_user_orm:
                raise exc.DatabaseError(
                    message=(_("Updated user could not be fetched from the database")),
                    detail={"id": user_id},
                )
        else:
            updated_user_orm = user_orm
        return UserResponseAdmin.model_validate(updated_user_orm)

    @invalidate_cache(DETAIL_PATTERN, LIST_PATTERN)
    async def delete_user(self, *, user_id: int, perm: bool = False) -> None:
        user: UserORM = await self._get_user_orm_by_id(user_id, perm)

        await self.crud.delete(self.db, obj_orm=user, perm=perm)
