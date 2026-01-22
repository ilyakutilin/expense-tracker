from datetime import datetime, timezone
from typing import Annotated, Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.security import decode_access_token
from app.core.cache import cached
from app.core.db import get_db_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import UserORM, UserRole
from app.schemas.auth import UserDep
from app.schemas.cache import CachePattern, Entity

# OAuth2 scheme - this tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@cached(
    pattern=CachePattern(entity=Entity.USER, obj_id_key="user_id", is_user_owned=False),
    response_model=UserDep,
    expire=12 * 60 * 60,
)
async def get_user_instance(db: AsyncSession, *, user_id: int) -> UserDep | None:
    result = await db.execute(
        select(UserORM).where(and_(UserORM.id_ == user_id, UserORM.is_active))
    )
    user_orm: UserORM | None = result.scalar_one_or_none()
    if user_orm:
        return UserDep.model_validate(user_orm)

    return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserDep:
    """
    Dependency to get the current user from JWT token.
    Validates token, checks user existence and returns a UserDep instance.

    Args:
        token: JWT token from Authorization header
        db: Async database session

    Returns:
        Current User instance

    Raises:
        UnauthorizedError: If token is invalid or expired or user not found
    """
    credentials_exception = UnauthorizedError(
        message="Could not validate credentials",
    )

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    exp = datetime.fromtimestamp(float(payload.get("exp", 0)), tz=timezone.utc)
    now = datetime.now(timezone.utc)
    if exp <= now:
        raise credentials_exception

    user: UserDep | None = await get_user_instance(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user


def require_roles(allowed_roles: list[UserRole]) -> Callable:
    """Factory function that returns a dependency checking for specific roles"""

    def role_checker(current_user: UserDep = Depends(get_current_user)) -> UserDep:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                message="Insufficient permissions",
                detail={
                    "user_id": current_user.id_,
                    "user_role": current_user.role.value,
                },
            )

        return current_user

    return role_checker


require_user = require_roles([UserRole.USER, UserRole.ADMIN])
require_admin = require_roles([UserRole.ADMIN])
