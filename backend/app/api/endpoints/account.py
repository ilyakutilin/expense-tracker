from fastapi import APIRouter, Depends, status

from app.api.deps import get_account_service
from app.schemas.account import AccountCreate, AccountResponse
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
async def create_new_currency(
    account_data: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    return await account_service.create_account(account_data)
