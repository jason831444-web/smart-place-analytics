"""add seat usage factor to facilities

Revision ID: 0002_add_seat_usage_factor
Revises: 0001_initial
Create Date: 2026-04-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_seat_usage_factor"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "facilities",
        sa.Column("seat_usage_factor", sa.Float(), nullable=False, server_default="1.0"),
    )
    op.alter_column("facilities", "seat_usage_factor", server_default=None)


def downgrade() -> None:
    op.drop_column("facilities", "seat_usage_factor")