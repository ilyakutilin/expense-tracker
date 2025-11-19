from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import BaseModelNoTimestampsORM


class CurrencyORM(BaseModelNoTimestampsORM):
    code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
