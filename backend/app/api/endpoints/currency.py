from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.crud import currency_crud
from app.models import CurrencyORM
from app.schemas import CurrencyCreate, CurrencyDB

router = APIRouter()


@router.post("/", response_model=CurrencyDB, status_code=status.HTTP_201_CREATED)
async def create_new_currency(
    currency_data: CurrencyCreate, db_session: AsyncSession = Depends(get_db_session)
) -> CurrencyDB:
    db_obj: CurrencyORM = await currency_crud.create_currency(currency_data, db_session)
    return CurrencyDB.model_validate(db_obj, by_alias=True)
