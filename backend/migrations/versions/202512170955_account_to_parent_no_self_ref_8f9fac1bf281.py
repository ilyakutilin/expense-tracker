"""Account to parent no self ref

Revision ID: 8f9fac1bf281
Revises: bcafc871a766
Create Date: 2025-12-17 09:55:32.340268

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f9fac1bf281"
down_revision: Union[str, Sequence[str], None] = "bcafc871a766"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "account_parent_no_self_reference",
        "account",
        "id != parent_id",
    )


def downgrade() -> None:
    op.drop_constraint(
        "account_parent_no_self_reference",
        "account",
        type_="check",
    )
