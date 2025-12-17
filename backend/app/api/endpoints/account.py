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


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_new_account(
    account_data: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.create_account(account_data)


@router.patch(
    "/{account_id}", response_model=AccountResponse, status_code=status.HTTP_200_OK
)
async def update_currency(
    account_id: int,
    account_update: AccountUpdate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.update_account(account_id, account_update)
