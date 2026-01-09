from pydantic import ConfigDict, Field

from app.filters.base import (
    BaseFilterParams,
    FilterField,
    FilterManager,
    FilterOperator,
    OrderField,
    SearchField,
)
from app.models.account import AccountORM
from app.schemas.account import AccountType

account_filter_manager = FilterManager(
    model_class=AccountORM,
    filter_fields={
        "type_": FilterField(column=AccountORM.type_, operator=FilterOperator.EQ),
    },
    order_fields={
        "id": OrderField(column=AccountORM.id_),
        "name": OrderField(column=AccountORM.name),
        "type": OrderField(column=AccountORM.type_),
        "created_at": OrderField(column=AccountORM.created_at),
        "updated_at": OrderField(column=AccountORM.updated_at),
    },
    search_fields=[
        SearchField(column=AccountORM.name),
    ],
)


class AccountFilterParams(BaseFilterParams):
    """Filter parameters for accounts"""

    type_: AccountType | None = Field(None, alias="type")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def manager(self) -> FilterManager:
        return account_filter_manager
