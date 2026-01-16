from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.security import decode_access_token
from app.core.cache import get_from_cache, set_cache
from app.core.db import get_db_session
from app.core.exceptions import UnauthorizedError
from app.models.user import UserORM

# OAuth2 scheme - this tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def _user_exists(db: AsyncSession, user_id: int) -> bool:
    key = f"user:exists:{user_id}"
    result = await get_from_cache(key)
    if result is None:
        result = await db.execute(
            select(UserORM.id_).where(and_(UserORM.id_ == user_id, UserORM.is_active))
        )
        result = result.scalar_one_or_none() is not None
        await set_cache(key, int(result))

    return bool(int(result))


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> int:
    """
    Dependency to get the current user's ID from JWT token.
    Validates token and checks user exists.

    Args:
        token: JWT token from Authorization header
        db: Async database session

    Returns:
        Current user's ID

    Raises:
        UnauthorizedError: If token is invalid or expired or user not found
    """
    credentials_exception = UnauthorizedError(
        message="Could not validate credentials",
        detail={"headers": {"WWW-Authenticate": "Bearer"}},
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

    user_exists = await _user_exists(db, user_id)
    if not user_exists:
        raise credentials_exception

    return user_id
