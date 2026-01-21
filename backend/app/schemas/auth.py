from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from app.models.user import UserRole


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: SecretStr = Field(..., min_length=8, max_length=100, exclude=True)
    password_hash: str | None = None


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: SecretStr


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""

    user_id: int | None = None


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id_: int = Field(..., serialization_alias="id")
    email: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDep(BaseModel):
    """Schema for the user dependency."""

    id_: int
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
