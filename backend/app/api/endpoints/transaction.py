from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_transaction_service
from app.filters.transaction import TransactionFilterParams
from app.schemas.pagination import PaginatedResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import TransactionService

router = APIRouter()


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_one_transaction(
    transaction_id: int,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await transaction_service.get_transaction_by_id(
        transaction_id=transaction_id
    )


@router.get(
    "/",
    response_model=PaginatedResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_transactions(
    transaction_service: TransactionService = Depends(get_transaction_service),
    filter_params: TransactionFilterParams = Depends(),
    incl_deleted: bool = Query(
        default=False, description="Include transactions in trash"
    ),
) -> PaginatedResponse[TransactionResponse]:
    return await transaction_service.get_all_transactions(
        filter_params=filter_params,
        include_deleted=incl_deleted,
    )


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_transaction(
    transaction_data: TransactionCreate,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await transaction_service.create_transaction(tc=transaction_data)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await transaction_service.update_transaction(
        transaction_id=transaction_id, tu=transaction_update
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    perm: bool = False,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> None:
    await transaction_service.delete_transaction(
        transaction_id=transaction_id, perm=perm
    )
