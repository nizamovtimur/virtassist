"""change timestamps to created_at, updated_at

Revision ID: 45011126aa97
Revises: 8ca184e36b11
Create Date: 2024-05-27 11:05:38.252698

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "45011126aa97"
down_revision: Union[str, None] = "8ca184e36b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("user", "time_created", new_column_name="created_at")
    op.alter_column("question_answer", "time_created", new_column_name="created_at")
    op.alter_column("chunk", "time_created", new_column_name="created_at")
    op.alter_column("admin", "time_created", new_column_name="created_at")
    op.alter_column("user", "time_updated", new_column_name="updated_at")
    op.alter_column("question_answer", "time_updated", new_column_name="updated_at")
    op.alter_column("chunk", "time_updated", new_column_name="updated_at")
    op.alter_column("admin", "time_updated", new_column_name="updated_at")


def downgrade() -> None:
    pass
