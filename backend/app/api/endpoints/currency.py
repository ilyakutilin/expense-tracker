from fastapi import APIRouter, Depends, status

from app.api.deps import get_currency_service
from app.schemas import CurrencyCreate, CurrencyResponse, CurrencyUpdate
from app.services.currency_service import CurrencyService

router = APIRouter()


@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_currency(
    currency_data: CurrencyCreate,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyResponse:
    return await currency_service.create_currency(currency_data)


@router.patch(
    "/{currency_id}", response_model=CurrencyResponse, status_code=status.HTTP_200_OK
)
async def update_currency(
    currency_id: int,
    currency_data: CurrencyUpdate,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyResponse:
    return await currency_service.update_currency(currency_id, currency_data)


@router.get("/", response_model=list[CurrencyResponse], status_code=status.HTTP_200_OK)
async def get_all_currencies(
    currency_service: CurrencyService = Depends(get_currency_service),
) -> list[CurrencyResponse]:
    return await currency_service.get_all_currencies()


@router.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_currency(
    currency_id: int,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> None:
    await currency_service.soft_delete_currency(currency_id)
