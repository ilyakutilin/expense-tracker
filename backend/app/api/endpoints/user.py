from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_user_service
from app.filters.user import UserFilterParams
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserCreate, UserResponseAdmin, UserUpdate
from app.services import UserService

router = APIRouter()


@router.get(
    "/{user_id}", response_model=UserResponseAdmin, status_code=status.HTTP_200_OK
)
async def get_one_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
) -> UserResponseAdmin:
    return await user_service.get_user_by_id(user_id=user_id)


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponseAdmin],
    status_code=status.HTTP_200_OK,
)
async def get_all_users(
    user_service: UserService = Depends(get_user_service),
    filter_params: UserFilterParams = Depends(),
    incl_deleted: bool = Query(default=False, description="Include users in trash"),
) -> PaginatedResponse[UserResponseAdmin]:
    return await user_service.get_all_users(
        filter_params=filter_params,
        include_deleted=incl_deleted,
    )


@router.post("/", response_model=UserResponseAdmin, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponseAdmin:
    return await user_service.create_user(user_create=user_data)


@router.patch(
    "/{user_id}", response_model=UserResponseAdmin, status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponseAdmin:
    return await user_service.update_user(user_id=user_id, user_update=user_update)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    perm: bool = False,
    user_service: UserService = Depends(get_user_service),
) -> None:
    await user_service.delete_user(user_id=user_id, perm=perm)
