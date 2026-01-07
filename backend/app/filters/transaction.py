from datetime import date
from decimal import Decimal

from pydantic import ConfigDict, Field
from sqlalchemy import exists, select

from app.filters.base import (
    BaseFilterParams,
    FilterField,
    FilterManager,
    FilterOperator,
    OrderField,
    SearchField,
)
from app.models.transaction import TransactionLineORM, TransactionORM, transaction_tag
from app.schemas.transaction import TransactionType


class TransactionFilterParams(BaseFilterParams):
    """Filter parameters for transactions"""

    # Direct transaction fields
    type_: TransactionType | None = Field(None, alias="type")
    date_lt: date | None = None
    date_lte: date | None = None
    date_gt: date | None = None
    date_gte: date | None = None
    comment: str | None = None
    is_template: bool | None = None

    # Transaction line filters (related)
    account_id: int | None = None
    account_id_in: str | None = None  # Comma-separated
    amount_lt: Decimal | None = None
    amount_lte: Decimal | None = None
    amount_gt: Decimal | None = None
    amount_gte: Decimal | None = None

    # Tag filters (many-to-many)
    tag_ids_in: str | None = None  # Comma-separated
    tag_ids_all: str | None = None  # Comma-separated - must have ALL these tags

    model_config = ConfigDict(populate_by_name=True)


def parse_comma_separated_ints(value: str) -> list[int]:
    """Parse comma-separated string to list of integers"""
    return [int(x.strip()) for x in value.split(",") if x.strip()]


# Build subquery conditions for related tables
def account_id_subquery(account_id: int, model_class):
    """Filter transactions that have a line with this account_id"""
    return exists(
        select(1)
        .where(TransactionLineORM.transaction_id == model_class.id_)
        .where(TransactionLineORM.account_id == account_id)
    )


def account_id_in_subquery(account_ids: list[int], model_class):
    """Filter transactions that have a line with any of these account_ids"""
    return exists(
        select(1)
        .where(TransactionLineORM.transaction_id == model_class.id_)
        .where(TransactionLineORM.account_id.in_(account_ids))
    )


def amount_comparison_subquery(operator: str):
    """Factory for amount comparison subqueries"""

    def subquery(amount: Decimal, model_class):
        stmt = select(1).where(TransactionLineORM.transaction_id == model_class.id_)

        if operator == "lt":
            stmt = stmt.where(TransactionLineORM.amount < amount)
        elif operator == "lte":
            stmt = stmt.where(TransactionLineORM.amount <= amount)
        elif operator == "gt":
            stmt = stmt.where(TransactionLineORM.amount > amount)
        elif operator == "gte":
            stmt = stmt.where(TransactionLineORM.amount >= amount)

        return exists(stmt)

    return subquery


def tag_ids_in_subquery(tag_ids: list[int], model_class):
    """Filter transactions that have any of these tags"""
    return exists(
        select(1)
        .select_from(transaction_tag)
        .where(transaction_tag.c.transaction_id == model_class.id_)
        .where(transaction_tag.c.tag_id.in_(tag_ids))
    )


def tag_ids_all_subquery(tag_ids: list[int], model_class):
    """Filter transactions that have ALL of these tags"""
    from sqlalchemy import func

    # Count how many of the specified tags this transaction has
    # It must equal the number of tags we're looking for
    return exists(
        select(1)
        .select_from(transaction_tag)
        .where(transaction_tag.c.transaction_id == model_class.id_)
        .where(transaction_tag.c.tag_id.in_(tag_ids))
        .group_by(transaction_tag.c.transaction_id)
        .having(func.count(transaction_tag.c.tag_id) == len(tag_ids))
    )


# Create the filter manager
transaction_filter_manager = FilterManager(
    model_class=TransactionORM,
    filter_fields={
        "type_": FilterField(column=TransactionORM.type_, operator=FilterOperator.EQ),
        "date_lt": FilterField(column=TransactionORM.date, operator=FilterOperator.LT),
        "date_lte": FilterField(
            column=TransactionORM.date, operator=FilterOperator.LTE
        ),
        "date_gt": FilterField(column=TransactionORM.date, operator=FilterOperator.GT),
        "date_gte": FilterField(
            column=TransactionORM.date, operator=FilterOperator.GTE
        ),
        "comment": FilterField(
            column=TransactionORM.comment, operator=FilterOperator.ILIKE
        ),
        "is_template": FilterField(
            column=TransactionORM.is_template, operator=FilterOperator.EQ
        ),
        "account_id": FilterField(subquery_builder=account_id_subquery),
        "account_id_in": FilterField(
            preprocessor=parse_comma_separated_ints,
            subquery_builder=account_id_in_subquery,
        ),
        "amount_lt": FilterField(subquery_builder=amount_comparison_subquery("lt")),
        "amount_lte": FilterField(subquery_builder=amount_comparison_subquery("lte")),
        "amount_gt": FilterField(subquery_builder=amount_comparison_subquery("gt")),
        "amount_gte": FilterField(subquery_builder=amount_comparison_subquery("gte")),
        "tag_ids_in": FilterField(
            preprocessor=parse_comma_separated_ints,
            subquery_builder=tag_ids_in_subquery,
        ),
        "tag_ids_all": FilterField(
            preprocessor=parse_comma_separated_ints,
            subquery_builder=tag_ids_all_subquery,
        ),
    },
    order_fields={
        "id": OrderField(column=TransactionORM.id_),
        "type": OrderField(column=TransactionORM.type_),
        "date": OrderField(column=TransactionORM.date),
        "is_template": OrderField(column=TransactionORM.is_template),
    },
    search_fields=[
        SearchField(column=TransactionORM.comment),
    ],
)
