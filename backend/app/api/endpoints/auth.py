# app/api/auth.py

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_service
from app.core.auth.dependency import get_current_user
from app.schemas.auth import Token, UserDep, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data (email and password)
        auth_service: Auth service instance

    Returns:
        Created user data (without password)

    Raises:
        HTTPException: If user with email already exists
    """
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Login and get access token.

    Uses OAuth2 password flow - accepts username and password in form data.
    Note: 'username' field should contain the email address.

    Args:
        form_data: OAuth2 form with username (email) and password
        auth_service: Auth service instance

    Returns:
        Access token and token type

    Raises:
        HTTPException: If credentials are invalid
    """
    return await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    auth_service: AuthService = Depends(get_auth_service),
    user: UserDep = Depends(get_current_user),
) -> UserResponse:
    return await auth_service.get_user_by_id(user.id_)
