from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_currency_service
from app.filters.currency import CurrencyFilterParams
from app.schemas.currency import CurrencyCreate, CurrencyResponse, CurrencyUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.currency_service import CurrencyService

router = APIRouter()


@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_currency(
    currency_data: CurrencyCreate,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyResponse:
    return await currency_service.create_currency(currency_create=currency_data)


@router.patch(
    "/{currency_id}", response_model=CurrencyResponse, status_code=status.HTTP_200_OK
)
async def update_currency(
    currency_id: int,
    currency_data: CurrencyUpdate,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyResponse:
    return await currency_service.update_currency(
        currency_id=currency_id, currency_update=currency_data
    )


@router.get(
    "/",
    response_model=PaginatedResponse[CurrencyResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_currencies(
    currency_service: CurrencyService = Depends(get_currency_service),
    filter_params: CurrencyFilterParams = Depends(),
    incl_deleted: bool = Query(
        default=False, description="Include currencies in trash"
    ),
) -> PaginatedResponse[CurrencyResponse]:
    return await currency_service.get_all_currencies(
        filter_params=filter_params, include_deleted=incl_deleted
    )


@router.get(
    "/{currency_id}", response_model=CurrencyResponse, status_code=status.HTTP_200_OK
)
async def get_currency(
    currency_id: int,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyResponse:
    return await currency_service.get_currency(currency_id=currency_id)


@router.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency(
    currency_id: int,
    perm: bool = False,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> None:
    await currency_service.delete_currency(currency_id=currency_id, perm=perm)
