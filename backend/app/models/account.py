from decimal import Decimal
from typing import TYPE_CHECKING

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field, field_validator
from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.settings import settings
from app.models.base import BaseORM

if TYPE_CHECKING:
    from app.models.currency import CurrencyORM
    from app.models.operation import OperationORM


class AccountORM(BaseORM):
    name: Mapped[str] = mapped_column(Text)
    type_: Mapped[str] = mapped_column("type", Text, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"), index=True
    )
    currency_id: Mapped[int | None] = mapped_column(
        ForeignKey("currency.id", ondelete="RESTRICT"), index=True
    )
    balance: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=settings.NUMERIC_PRECISION,
            scale=settings.NUMERIC_SCALE,
            decimal_return_scale=settings.NUMERIC_SCALE,
            asdecimal=True,
        ),
        default=Decimal("0.0"),
    )

    parent: Mapped["AccountORM | None"] = relationship(
        "AccountORM",
        remote_side="AccountORM.id_",
        back_populates="children",
        foreign_keys=[parent_id],
    )

    children: Mapped[list["AccountORM"]] = relationship(
        "AccountORM",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    currency: Mapped["CurrencyORM"] = relationship(
        "CurrencyORM",
        back_populates="accounts",
    )

    operations_from: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        foreign_keys="[OperationORM.from_acc_id]",
        back_populates="from_acc",
    )

    operations_to: Mapped[list["OperationORM"]] = relationship(
        "OperationORM",
        foreign_keys="[OperationORM.to_acc_id]",
        back_populates="to_acc",
    )

    # Hybrid relationship that combines both from and to operations
    operations: Mapped[list["OperationORM"]] = relationship(
        primaryjoin="or_(AccountORM.id_==OperationORM.from_acc_id, AccountORM.id_==OperationORM.to_acc_id)",
        viewonly=True,
        lazy="select",
        overlaps="from_acc,to_acc",  # Important to avoid conflicts
    )

    __table_args__ = (
        Index(
            "ix_account_unique_name_active",
            "name",
            unique=True,
            postgresql_where=(text("is_deleted = false")),
        ),
        CheckConstraint("id != parent_id", name="account_parent_no_self_reference"),
    )


class AccountFilter(Filter):
    type_: str | None = Field(None, alias="type")
    type__in: list[str] | None = None

    order_by: list[str] = ["id"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = AccountORM
        search_model_fields = ["name"]

    @field_validator("order_by")
    def restrict_sortable_fields(cls, value):
        if value is None:
            return None

        allowed_field_names = [
            "id",
            "name",
            "type",
            "balance",
            "created_at",
            "updated_at",
        ]

        for field_name in value:
            field_name = field_name.replace("+", "").replace("-", "")  #
            if field_name not in allowed_field_names:
                raise ValueError(
                    f"You may only sort by: {', '.join(allowed_field_names)}"
                )

        return value
