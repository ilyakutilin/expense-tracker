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
from app.models.user import UserORM
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud: crud.CRUDUser = crud.user_crud

    async def _check_user_exists(self, email: str) -> None:
        exists: bool = await self.crud.exists(self.db, email=email)
        if exists:
            raise exc.ConflictError(
                message=f"User with email '{email}' already exists",
                detail={"email": email},
            )

    async def _get_user_orm_by_id(
        self, user_id: int, include_deleted: bool = False
    ) -> UserORM:
        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db, user_id, include_deleted
        )
        if not user_orm:
            raise exc.NotFoundError(
                message=f"User with id {user_id} not found",
                detail={"id": user_id},
            )
        return user_orm

    async def register_user(self, user_register: UserRegister) -> UserResponse:
        await self._check_user_exists(email=user_register.email)

        hashed_password = get_password_hash(str(user_register.password))
        user_register.password_hash = hashed_password
        user_data: dict[str, Any] = user_register.model_dump()
        user_id: int = await self.crud.create(self.db, user_data, commit=True)

        user_orm: UserORM | None = await self.crud.get_by_id(
            self.db, user_id, include_deleted=False
        )
        if not user_orm:
            raise exc.DatabaseError(
                message=("Created user could not be fetched from the database"),
                detail={"id": user_id, "email": user_register.email},
            )
        return UserResponse.model_validate(user_orm)

    async def authenticate_user(self, user_login: UserLogin) -> UserResponse | None:
        user_orm: UserORM | None = await self.crud.get_by(
            self.db, include_deleted=False, email=user_login.email
        )

        if not user_orm:
            return None

        if not verify_password(str(user_login.password), user_orm.password_hash):
            return None

        return UserResponse.model_validate(user_orm)

    def create_token_for_user(self, user_id: int) -> Token:
        access_token = create_access_token(
            data={"sub": str(user_id)},  # "sub" is the standard JWT claim for subject
        )

        return Token(access_token=access_token, token_type="bearer")

    async def get_user_by_id(
        self, user_id: int, include_deleted: bool = False
    ) -> UserResponse:
        user_orm: UserORM = await self._get_user_orm_by_id(user_id, include_deleted)
        return UserResponse.model_validate(user_orm)
