from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=8, max_length=100, exclude=True)
    role: UserRole


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: SecretStr | None = Field(None, min_length=8, max_length=100, exclude=True)
    role: UserRole | None = None


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id_: int = Field(..., serialization_alias="id")
    email: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponseAdmin(UserResponse):
    is_deleted: bool
    deleted_at: datetime | None
