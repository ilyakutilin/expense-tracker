from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class CreatedUpdatedMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        sort_order=98,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        sort_order=99,
    )
