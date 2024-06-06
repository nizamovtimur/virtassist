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
    op.drop_table("chunk")
    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("confluence_url", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("chunk")
    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("confluence_url", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=312), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
