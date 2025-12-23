from fastapi import APIRouter, Depends, Query, status
from fastapi_filter import FilterDepends

from app.api.deps import get_transaction_service
from app.models.transaction import TransactionFilter
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
    return await transaction_service.get_transaction_by_id(transaction_id)


@router.get(
    "/",
    response_model=PaginatedResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_transactions(
    transaction_service: TransactionService = Depends(get_transaction_service),
    transaction_filter: TransactionFilter = FilterDepends(
        TransactionFilter, by_alias=True
    ),
    incl_deleted: bool = Query(
        default=False, description="Include transactions in trash"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[TransactionResponse]:
    return await transaction_service.get_all_transactions(
        include_deleted=incl_deleted,
        filter_=transaction_filter,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_transaction(
    transaction_data: TransactionCreate,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    return await transaction_service.create_transaction(transaction_data)


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
        transaction_id, transaction_update
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    perm: bool = False,
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> None:
    await transaction_service.delete_transaction(transaction_id, perm)
