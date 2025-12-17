from fastapi import APIRouter, Depends, status

from app.api.deps import get_account_service
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services import AccountService

router = APIRouter()


@router.get(
    "/{account_id}", response_model=AccountResponse, status_code=status.HTTP_200_OK
)
async def get_one_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.get_account_by_id(account_id)


@router.get("/", response_model=list[AccountResponse], status_code=status.HTTP_200_OK)
async def get_all_accounts(
    account_service: AccountService = Depends(get_account_service),
) -> list[AccountResponse]:
    return await account_service.get_all_accounts()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_new_account(
    account_data: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.create_account(account_data)


@router.patch(
    "/{account_id}", response_model=AccountResponse, status_code=status.HTTP_200_OK
)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.update_account(account_id, account_update)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    perm: bool = False,
    account_service: AccountService = Depends(get_account_service),
) -> None:
    await account_service.delete_account(account_id, perm)
