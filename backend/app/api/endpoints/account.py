from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_account_service
from app.filters.account import AccountFilterParams
from app.schemas.account import (
    AccountCreate,
    AccountResponseFlat,
    AccountResponseTree,
    AccountUpdate,
)
from app.services import AccountService

router = APIRouter()


@router.get(
    "/{account_id}", response_model=AccountResponseFlat, status_code=status.HTTP_200_OK
)
async def get_one_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponseFlat:
    return await account_service.get_account_by_id(account_id=account_id)


@router.get(
    "/",
    response_model=list[AccountResponseTree],
    status_code=status.HTTP_200_OK,
)
async def get_all_accounts(
    account_service: AccountService = Depends(get_account_service),
    filter_params: AccountFilterParams = Depends(),
    incl_deleted: bool = Query(default=False, description="Include accounts in trash"),
) -> list[AccountResponseTree]:
    return await account_service.get_all_accounts(
        filter_params=filter_params,
        include_deleted=incl_deleted,
    )


@router.post(
    "/", response_model=AccountResponseFlat, status_code=status.HTTP_201_CREATED
)
async def create_new_account(
    account_data: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponseFlat:
    return await account_service.create_account(account_create=account_data)


@router.patch(
    "/{account_id}", response_model=AccountResponseFlat, status_code=status.HTTP_200_OK
)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponseFlat:
    return await account_service.update_account(
        account_id=account_id, account_update=account_update
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    perm: bool = False,
    account_service: AccountService = Depends(get_account_service),
) -> None:
    await account_service.delete_account(account_id=account_id, perm=perm)
