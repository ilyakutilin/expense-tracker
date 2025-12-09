from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import CurrencyORM


class CRUDCurrency(CRUDBase[CurrencyORM]):
    # Note: No __init__ needed if you are just relying on the base methods.
    # If you *do* add an __init__, you still need to call the parent __init__
    # and pass the specific model:
    # def __init__(self) -> None:
    #     super().__init__(model=CurrencyORM)
    async def get_currency_by_code(
        self,
        db_session: AsyncSession,
        code: str,
    ) -> CurrencyORM | None:
        query = select(CurrencyORM).where(
            and_(CurrencyORM.code == code, CurrencyORM.is_active)
        )
        result = await db_session.execute(query)
        return result.scalar_one_or_none()


currency_crud = CRUDCurrency(CurrencyORM)
