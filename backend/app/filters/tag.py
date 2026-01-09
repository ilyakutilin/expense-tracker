from pydantic import ConfigDict

from app.filters.base import (
    BaseFilterParams,
    FilterField,
    FilterManager,
    FilterOperator,
    OrderField,
    SearchField,
)
from app.models.tag import TagORM

tag_filter_manager = FilterManager(
    model_class=TagORM,
    filter_fields={
        "name": FilterField(column=TagORM.name, operator=FilterOperator.EQ),
        "transactions_count_lt": FilterField(
            column=TagORM.transactions_count, operator=FilterOperator.LT
        ),
        "transactions_count_lte": FilterField(
            column=TagORM.transactions_count, operator=FilterOperator.LTE
        ),
        "transactions_count_gt": FilterField(
            column=TagORM.transactions_count, operator=FilterOperator.GT
        ),
        "transactions_count_gte": FilterField(
            column=TagORM.transactions_count, operator=FilterOperator.GTE
        ),
    },
    order_fields={
        "id": OrderField(column=TagORM.id_),
        "name": OrderField(column=TagORM.name),
        "created_at": OrderField(column=TagORM.created_at),
        "updated_at": OrderField(column=TagORM.updated_at),
        "transactions_count": OrderField(column=TagORM.transactions_count),
    },
    search_fields=[
        SearchField(column=TagORM.name),
    ],
)


class TagFilterParams(BaseFilterParams):
    """Filter parameters for tags"""

    model_config = ConfigDict(populate_by_name=True)

    @property
    def manager(self) -> FilterManager:
        return tag_filter_manager
