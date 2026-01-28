# app/services/auth_service.py

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core import exceptions as exc
from app.core.auth.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.core.cache import cached
from app.core.i18n import _
from app.models.user import UserORM, UserRole
from app.schemas.auth import Token, UserRegister
from app.schemas.cache import CachePattern, Entity
from app.schemas.user import UserResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDUser = crud.user_crud

    async def _check_user_exists(self, email: str) -> None:
        exists: bool = await self.crud.exists(self.db, email=email)
        if exists:
            raise exc.ConflictError(
                translatable_message=_("User with email '{email}' already exists"),
                email=email,
                detail={"email": email},
            )

    async def _get_user_orm_by_id(
        self, user_id: int, include_deleted: bool = False
    ) -> UserORM:
        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db, obj_id=user_id, include_deleted=include_deleted
        )
        if not user_orm:
            raise exc.NotFoundError(
                translatable_message=_("User with id {user_id} not found"),
                user_id=user_id,
                detail={"id": user_id},
            )
        return user_orm

    async def register_user(self, user_register: UserRegister) -> UserResponse:
        await self._check_user_exists(email=user_register.email)

        user_data: dict[str, Any] = user_register.model_dump()
        hashed_password = get_password_hash(str(user_register.password))
        user_data["password_hash"] = hashed_password
        user_data["role"] = UserRole.USER.value
        user_id: int = await self.crud.create(self.db, obj_data=user_data, commit=True)

        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db, obj_id=user_id, include_deleted=False
        )
        if not user_orm:
            raise exc.DatabaseError(
                message="Created user could not be fetched from the database",
                detail={"id": user_id, "email": user_register.email},
            )
        return UserResponse.model_validate(user_orm)

    async def authenticate_user(self, email: str, password: str) -> Token:
        user_orm: UserORM | None = await self.crud.get_by(
            self.db, include_deleted=False, email=email
        )

        err = exc.UnauthorizedError(
            translatable_message=_("Incorrect email or password"),
        )

        if not user_orm:
            raise err

        if not verify_password(password, user_orm.password_hash):
            raise err

        access_token = create_access_token(data={"sub": str(user_orm.id_)})

        return Token(access_token=access_token, token_type="bearer")

    @cached(
        pattern=CachePattern(
            entity=Entity.USER,
            obj_id_key="user_id",
            is_user_owned=False,
        ),
        response_model=UserResponse,
    )
    async def get_user_by_id(
        self, user_id: int, include_deleted: bool = False
    ) -> UserResponse:
        user_orm: UserORM = await self._get_user_orm_by_id(user_id, include_deleted)
        return UserResponse.model_validate(user_orm)
