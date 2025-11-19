from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Identity
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.db import BaseORM


class BaseModelORM(BaseORM):
    __abstract__ = True

    id_: Mapped[int] = mapped_column(
        "id",
        BigInteger,
        Identity(
            always=True,
            start=1,
            increment=1,
            nominvalue=True,
            nomaxvalue=True,
            cycle=False,
        ),
        sort_order=-1,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        sort_order=98,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        sort_order=99,
    )
