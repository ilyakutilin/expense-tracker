# ruff: noqa: E501
# fmt: off

"""
Development data seeding script for expense tracker.
Run after migrations: python seed_dev_data.py
"""

import asyncio
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Delete, Table, TextClause, delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.security import get_password_hash
from app.core.settings import settings
from app.models.account import AccountORM
from app.models.base import BaseORM
from app.models.currency import CurrencyORM
from app.models.tag import TagORM
from app.models.transaction import TransactionLineORM, TransactionORM, transaction_tag
from app.models.user import UserORM
from app.schemas.account import AccountType
from app.schemas.transaction import TransactionType

# Minimum 33
START_DAYS_AGO = 33

NOW = datetime.now()

MAX_ACCOUNT_OFFSET_DAYS = 5
MAX_TRANSACTION_OFFSET_DAYS = 20

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24


class BaseData:
    def __init__(
        self,
        deleted: bool = False,
        _created_at: datetime | None = None,
        _updated_at: datetime | None = None,
        _deleted_at: datetime | None = None,
    ) -> None:
        self.deleted = deleted
        self._created_at = _created_at
        self._updated_at = _updated_at
        self._deleted_at = _deleted_at

    def _get_timedelta(self, ref_dt: datetime, now: datetime = datetime.now()) -> timedelta:
        lower_bound = 60
        upper_bound = int(now.timestamp() - ref_dt.timestamp()) - lower_bound
        seconds = random.randint(lower_bound, upper_bound)
        microseconds = random.randint(0, 999999)
        return timedelta(seconds=seconds, microseconds=microseconds)

    @property
    def created_at(self) -> datetime:
        return _generate_offset_datetime(NOW, "d", -START_DAYS_AGO + 1)

    @property
    def updated_at(self) -> datetime:
        if self._updated_at is None:
            same_as_created = random.choice((True,) * 4 + (False,))
            if same_as_created:
                self._updated_at = self.created_at
            else:
                self._updated_at = self.created_at + self._get_timedelta(self.created_at, NOW)
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        if not self.deleted:
            return None

        if self._deleted_at is None:
            self._deleted_at = NOW - self._get_timedelta(self.updated_at, NOW)

        return self._deleted_at


def _generate_offset_datetime(
    start_date: datetime,
    offset_mode: str = "s",
    offset: int = 0,
) -> datetime:
    valid_offset_modes = ("s", "m", "h", "d")
    if offset_mode not in valid_offset_modes:
        raise ValueError((f"{offset_mode} is not a valid offset mode. Use one of {', '.join(valid_offset_modes)}"))

    seconds = 0
    microseconds = random.randint(0, 999999)
    match offset_mode:
        case "d":
            seconds = DAY * offset + random.randint(0, DAY - 1)
        case "h":
            seconds = HOUR * offset + random.randint(0, HOUR - 1)
        case "m":
            seconds = MINUTE * offset + random.randint(0, MINUTE - 1)
        case "s":
            seconds = offset

    delta = timedelta(seconds=seconds, microseconds=microseconds)

    return start_date + delta


def _get_user_orms() -> tuple[UserORM, UserORM, UserORM]:
    admin = UserORM(
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword"),
        created_at=_generate_offset_datetime(NOW, "d", -START_DAYS_AGO),
        updated_at=_generate_offset_datetime(NOW, "d", -7),
        is_deleted=False,
        deleted_at=None,
    )
    regular_user = UserORM(
        email="john.smith@example.com",
        password_hash=get_password_hash("userpassword"),
        created_at=_generate_offset_datetime(admin.created_at, "d", 1),
        updated_at=_generate_offset_datetime(NOW, "d", -4),
        is_deleted=False,
        deleted_at=None,
    )
    timestamp = _generate_offset_datetime(admin.created_at, "d", 2)
    deleted_user = UserORM(
        email="deleted.user@example.com",
        password_hash=get_password_hash("deletedpassword"),
        created_at=timestamp,
        updated_at=timestamp,
        is_deleted=True,
        deleted_at=datetime.now() - timedelta(days=1),
    )

    return admin, regular_user, deleted_user


def _get_currency_orms(user: UserORM) -> list[CurrencyORM]:
    class CurrencyData(BaseData):
        def __init__(
            self,
            code: str,
            symbol: str | None,
            deleted: bool = False,
        ) -> None:
            self.code = code
            self.symbol = symbol
            super().__init__(deleted)

        @property
        def created_at(self) -> datetime:
            charsum = sum([ord(char) for char in self.code])
            max_charsum = ord("z") * 5
            if charsum > max_charsum:
                charsum = max_charsum
            return _generate_offset_datetime(user.created_at, "s", charsum * 2)

    currency_data: list[CurrencyData] = [
        CurrencyData("RUB", "₽", False),
        CurrencyData("USD", "$", False),
        CurrencyData("EUR", "€", False),
        CurrencyData("GBP", "£", False),
        CurrencyData("USDT", None, False),
        CurrencyData("TRX", "₮", False),
        CurrencyData("DEL", None, True),
    ]

    currencies: list[CurrencyORM] = []

    for cd in currency_data:
        currencies.append(
            CurrencyORM(
                code=cd.code,
                symbol=cd.symbol,
                user_id=user.id_,
                created_at=cd.created_at,
                updated_at=cd.updated_at,
                is_deleted=cd.deleted,
                deleted_at=cd.deleted_at,
            )
        )

    return currencies


def _get_account_orms(user: UserORM, currencies: list[CurrencyORM]) -> dict[str, AccountORM]:
    timestamp = _generate_offset_datetime(user.created_at, "m", 10)
    savings = AccountORM(
        name="Накопления",
        type_=AccountType.ASSET.value,
        user_id=user.id_,
        created_at=timestamp,
        updated_at=timestamp,
    )

    timestamp = _generate_offset_datetime(user.created_at, "m", 15)
    expenses = AccountORM(
        name="Расходы",
        type_=AccountType.EXPENSE.value,
        user_id=user.id_,
        created_at=timestamp,
        updated_at=timestamp,
    )

    class AccountData(BaseData):
        def __init__(
            self,
            name: str,
            type_: AccountType,
            parent: AccountORM | None,
            currency_index: int,
            created_offset_days: int,
            deleted: bool = False,
        ) -> None:
            self.name = name
            self.type_ = type_
            self.parent = parent
            self.currency_index = currency_index
            self.created_offset_days = created_offset_days
            super().__init__(deleted)

        @property
        def created_at(self) -> datetime:
            if self._created_at is None:
                created_offset_days = self.created_offset_days
                if created_offset_days > MAX_ACCOUNT_OFFSET_DAYS:
                    created_offset_days = MAX_ACCOUNT_OFFSET_DAYS
                self._created_at = _generate_offset_datetime(timestamp, "d", created_offset_days)
            return self._created_at

    account_data: dict[str, AccountData] = {
        "debit": AccountData("Дебетовая карта", AccountType.ASSET, None, 0, 3, False),
        "cash": AccountData("Наличные", AccountType.ASSET, None, 0, 3, False),
        "savings": AccountData("Вклад", AccountType.ASSET, savings, 0, 5, False),
        "dollars": AccountData("Доллары под матрасом", AccountType.ASSET, savings, 1, 4, False),
        "groceries": AccountData("Продукты", AccountType.EXPENSE, expenses, 0, 4, False),
        "fun": AccountData("Развлечения", AccountType.EXPENSE, expenses, 0, 5, False),
        "clothes": AccountData("Одежда и обувь", AccountType.EXPENSE, expenses, 0, 5, False),
        "salary": AccountData("Зарплата", AccountType.INCOME, None, 0, 2, False),
        "blocked": AccountData("Заблокированная карта", AccountType.ASSET, None, 0, 5, True),
    }

    accounts: dict[str, AccountORM] = {
        "savings_parent": savings,
        "expenses_parent": expenses,
    }
    for key, acc in account_data.items():
        accounts[key] = AccountORM(
            name=acc.name,
            type_=acc.type_.value,
            user_id=user.id_,
            parent_id=acc.parent.id_ if acc.parent else None,
            currency_id=currencies[acc.currency_index].id_,
            created_at=acc.created_at,
            updated_at=acc.updated_at,
            is_deleted=acc.deleted,
            deleted_at=acc.deleted_at,
        )

    return accounts


def _get_tag_orms(user: UserORM, qty: int = 5) -> list[TagORM]:
    if qty <= 0:
        qty = 1

    tags = []
    for i in range(1, qty + 1):
        timestamp = _generate_offset_datetime(user.created_at, "d", i)
        tags.append(
            TagORM(
                name=f"Тег {i}",
                user_id=user.id_,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    return tags


def _get_transaction_orms(user: UserORM, accounts: dict[str, AccountORM], tags: list[TagORM]) -> list[TransactionORM]:
    class TransactionData(BaseData):
        def __init__(
            self,
            type_: TransactionType,
            date_offset_days: int,
            comment: str | None,
            is_template: bool,
            from_acc_key: str,
            from_amount: float,
            to_acc_key: str,
            to_amount: float,
            deleted: bool,
        ) -> None:
            self.type_ = type_
            self.date_offset_days = date_offset_days
            self.comment = comment
            self.is_template = is_template
            self.from_acc_key = from_acc_key
            self.from_amount = from_amount
            self.to_acc_key = to_acc_key
            self.to_amount = to_amount
            self.deleted = deleted
            super().__init__(deleted)

        @property
        def user_id(self) -> int:
            return user.id_

        @property
        def date(self) -> date:
            acc_created_at_dts = [acc.created_at for acc in accounts.values()]
            latest_acc_created_at = max(acc_created_at_dts)
            date_offset_days = self.date_offset_days
            if date_offset_days > MAX_TRANSACTION_OFFSET_DAYS:
                date_offset_days = MAX_TRANSACTION_OFFSET_DAYS
            dt = _generate_offset_datetime(latest_acc_created_at, "d", date_offset_days)
            return dt.date()

        @property
        def created_at(self) -> datetime:
            if self._created_at is None:
                dt = datetime.combine(self.date, datetime.min.time())
                lower_bound = 1 * 60 * 60
                upper_bound = 48 * 60 * 60
                seconds = random.randint(lower_bound, upper_bound)
                microseconds = random.randint(0, 999999)
                self._created_at = dt + timedelta(seconds=seconds, microseconds=microseconds)
            return self._created_at

    TD = TransactionData
    TT = TransactionType

    transaction_data: list[TransactionData] = [
        # type, date_offset, comment, is_template, from_acc_key, from_amount, to_acc_key, to_amount, deleted
        # debit, cash, savings, dollars, groceries, fun, clothes, salary, blocked
        TD(TT.INCOME, 1, "Подсчёт", False, "salary", 197899.23, "debit", 197899.23, False),
        TD(TT.TRANSFER, 1, "Перевод на вклад", False, "debit", 50000, "savings", 50000, False),
        TD(TT.EXCHANGE, 1, "Обмен валюты", False, "debit", 27212.39, "dollars", 350, False),
        TD(TT.EXPENSE, 1, "Продукты в Пятёрочке", True, "debit", 0, "groceries", 0, False),
        TD(TT.EXPENSE, 2, "Продукты в Пятёрочке", False, "debit", 2752.11, "groceries", 2752.11, False),
        TD(TT.TRANSFER, 2, "Снятие налички", False, "debit", 30000, "cash", 30000, False),
        TD(TT.EXPENSE, 2, "Катание на санях", False, "cash", 4000, "fun", 4000, False),
        TD(TT.EXPENSE, 3, "Подписка на онлайн кинотеатр", False, "debit", 299.99, "fun", 299.99, True),
        TD(TT.EXPENSE, 4, "Покупка одежды в магазине", False, "debit", 19590, "clothes", 19590, False),
        TD(TT.EXPENSE, 4, "Покупка одежды на рынке", False, "cash", 10000, "clothes", 10000, False),
        TD(TT.EXPENSE, 6, "Поход в ресторан", False, "debit", 12400, "fun", 12400, False),
        TD(TT.EXPENSE, 7, "Продукты в Пятёрочке", False, "debit", 1985.54, "groceries", 1985.54, False),
        TD(TT.EXPENSE, 8, "Продукты в Пятёрочке", False, "debit", 780.40, "groceries", 780.40, False),
        TD(TT.EXPENSE, 10, "Продукты в Пятёрочке", False, "debit", 1059.87, "groceries", 1059.87, False),
        TD(TT.EXPENSE, 10, "Экскурсия в Ярославль", False, "debit", 45900, "fun", 45900, False),
        TD(TT.INCOME, 15, "Аванс", False, "salary", 48750.37, "debit", 48750.37, False),
        TD(TT.EXCHANGE, 15, "Обмен валюты", False, "debit", 7774.53, "dollars", 100, False),
        TD(TT.EXPENSE, 15, "Продукты в Пятёрочке", False, "debit", 3455.40, "groceries", 3455.40, False),
        TD(TT.EXPENSE, 17, "Продукты в Пятёрочке", False, "debit", 1560.19, "groceries", 1560.19, False),
        TD(TT.EXPENSE, 18, "Катание на моноколесе", False, "cash", 2500, "fun", 2500, False),
        TD(TT.EXPENSE, 18, "Фото с медведем", False, "cash", 1000, "fun", 1000, False),
    ]

    transactions: list[TransactionORM] = []
    for td in transaction_data:
        transaction_orm = TransactionORM(
            type_=td.type_.value,
            date=td.date,
            comment=td.comment,
            is_template=td.is_template,
            user_id=td.user_id,
            created_at=td.created_at,
            updated_at=td.updated_at,
            is_deleted=td.deleted,
            deleted_at=td.deleted_at,
        )

        transaction_orm.lines.extend(
            [
                TransactionLineORM(
                    transaction_id=transaction_orm.id_,
                    account_id=accounts[td.from_acc_key].id_,
                    amount=Decimal(td.from_amount),
                    created_at=td.created_at,
                    updated_at=td.updated_at,
                    is_deleted=td.deleted,
                    deleted_at=td.deleted_at,
                ),
                TransactionLineORM(
                    transaction_id=transaction_orm.id_,
                    account_id=accounts[td.to_acc_key].id_,
                    amount=Decimal(td.to_amount),
                    created_at=td.created_at,
                    updated_at=td.updated_at,
                    is_deleted=td.deleted,
                    deleted_at=td.deleted_at,
                ),
            ]
        )

        if random.random() < 0.6:
            transaction_tags = random.sample(tags, random.randint(1, len(tags)))
            transaction_orm.tags.extend(transaction_tags)

        transactions.append(transaction_orm)

    return transactions


async def seed_data():
    """Populate database with test data."""

    if START_DAYS_AGO < 33:
        raise ValueError(f"{START_DAYS_AGO=}")

    async_engine = create_async_engine(settings.db_settings.db_url, echo=True, future=True)
    async_session = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(select(UserORM))
        if result.scalars().first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding database with test data...")

        # Create users
        admin, regular_user, deleted_user = _get_user_orms()
        session.add_all([admin, regular_user, deleted_user])
        await session.flush()

        # Create currencies
        currencies = _get_currency_orms(regular_user)
        session.add_all(currencies)
        await session.flush()

        # Create accounts
        accounts: dict[str, AccountORM] = _get_account_orms(regular_user, currencies)
        session.add_all(accounts.values())
        await session.flush()

        # Create tags
        tags = _get_tag_orms(regular_user)
        session.add_all(tags)

        # Create transactions
        transactions = _get_transaction_orms(regular_user, accounts, tags)
        session.add_all(transactions)
        await session.flush()

        # Commit all changes
        await session.commit()
        print("✓ Database seeded successfully!")
        print(f"  - Created {len([admin, regular_user, deleted_user])} users")
        print(f"  - Created {len(currencies)} currencies")
        print(f"  - Created {len(accounts)} accounts")
        print(f"  - Created {len(tags)} tags")
        print(f"  - Created {len(transactions)} transactions")


def _get_clear_stmts(table: Table | type[BaseORM]) -> tuple[Delete, TextClause]:
    delete_stmt = delete(table)
    reset_stmt = text("")

    if isinstance(table, Table):
        table_name = table.name

    elif issubclass(table, BaseORM):
        table_name = table.__tablename__
        sequence_name = f"{table_name}_id_seq"
        reset_stmt = text(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")

    else:
        raise ValueError(f"Wrong table type: {type(table)}")

    return delete_stmt, reset_stmt


async def clear_data():
    """Clear all data from database."""
    async_engine = create_async_engine(settings.db_settings.db_url, echo=True, future=True)
    async_session = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Delete in reverse order of dependencies
        for table in (transaction_tag, TransactionLineORM, TransactionORM, AccountORM, TagORM, CurrencyORM, UserORM):
            delete_stmt, reset_stmt = _get_clear_stmts(table)
            await session.execute(delete_stmt)
            await session.execute(reset_stmt)

        await session.commit()
        print("✓ All data cleared")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_data())
    else:
        asyncio.run(seed_data())
