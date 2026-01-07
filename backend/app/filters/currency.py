from pydantic import ConfigDict

from app.filters.base import (
    BaseFilterParams,
    FilterManager,
    OrderField,
    SearchField,
)
from app.models.currency import CurrencyORM

currency_filter_manager = FilterManager(
    model_class=CurrencyORM,
    filter_fields=dict(),
    order_fields={
        "id": OrderField(column=CurrencyORM.id_),
        "created_at": OrderField(column=CurrencyORM.created_at),
        "updated_at": OrderField(column=CurrencyORM.updated_at),
    },
    search_fields=[
        SearchField(column=CurrencyORM.code),
        SearchField(column=CurrencyORM.symbol),
    ],
)


class CurrencyFilterParams(BaseFilterParams):
    """Filter parameters for currencies"""

    model_config = ConfigDict(populate_by_name=True)

    @property
    def manager(self) -> FilterManager:
        return currency_filter_manager
