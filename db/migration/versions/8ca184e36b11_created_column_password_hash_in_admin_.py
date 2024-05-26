"""created column password_hash in Admin table.

Revision ID: 8ca184e36b11
Revises: 474ae8a7ef46
Create Date: 2024-05-26 14:02:15.911689

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8ca184e36b11"
down_revision: Union[str, None] = "474ae8a7ef46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("admin", sa.Column("password_hash", sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column(table_name="admin", column_name="password_hash")
