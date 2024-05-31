"""change embedding dimension from 312 to 1024 in table Chunk

Revision ID: 22dcc1a837cc
Revises: 45011126aa97
Create Date: 2024-05-31 12:25:11.609731

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "22dcc1a837cc"
down_revision: Union[str, None] = "45011126aa97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "chunk",
        "embedding",
        existing_type=Vector(312),
        type_=Vector(1024),
    )


def downgrade() -> None:
    op.alter_column(
        "chunk",
        "embedding",
        existing_type=Vector(312),
        type_=Vector(1024),
    )
