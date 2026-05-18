"""add facility operational rollups

Revision ID: 0004_add_operational_rollups
Revises: 0003_expand_occupancy_logs_add_sensor_logs
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_operational_rollups"
down_revision: Union[str, None] = "0003_expand_occupancy_logs_add_sensor_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facility_operational_rollups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("window_minutes", sa.Integer(), nullable=False),
        sa.Column("avg_occupancy_rate", sa.Float(), nullable=False),
        sa.Column("peak_occupancy_rate", sa.Float(), nullable=False),
        sa.Column("high_congestion_events", sa.Integer(), nullable=False),
        sa.Column("avg_power_kw", sa.Float(), nullable=True),
        sa.Column("peak_power_kw", sa.Float(), nullable=True),
        sa.Column("avg_temperature", sa.Float(), nullable=True),
        sa.Column("avg_noise_level", sa.Float(), nullable=True),
        sa.Column("recommendation_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_facility_operational_rollups_id"), "facility_operational_rollups", ["id"], unique=False)
    op.create_index(op.f("ix_facility_operational_rollups_facility_id"), "facility_operational_rollups", ["facility_id"], unique=False)
    op.create_index(op.f("ix_facility_operational_rollups_timestamp"), "facility_operational_rollups", ["timestamp"], unique=False)
    op.create_index(
        "ix_facility_operational_rollups_facility_window_timestamp",
        "facility_operational_rollups",
        ["facility_id", "window_minutes", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_facility_operational_rollups_facility_window_timestamp", table_name="facility_operational_rollups")
    op.drop_table("facility_operational_rollups")
