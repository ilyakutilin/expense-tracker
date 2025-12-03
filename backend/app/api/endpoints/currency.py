from fastapi import APIRouter, Depends, status

from app.api.deps import get_currency_service
from app.schemas import CurrencyCreate, CurrencyDB
from app.services.currency_service import CurrencyService

router = APIRouter()


@router.post("/", response_model=CurrencyDB, status_code=status.HTTP_201_CREATED)
async def create_new_currency(
    currency_data: CurrencyCreate,
    currency_service: CurrencyService = Depends(get_currency_service),
) -> CurrencyDB:
    return await currency_service.create_currency(currency_data)
