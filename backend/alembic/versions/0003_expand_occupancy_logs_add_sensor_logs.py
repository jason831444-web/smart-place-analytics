"""expand occupancy logs and add sensor logs

Revision ID: 0003_expand_occupancy_logs_add_sensor_logs
Revises: 0002_add_seat_usage_factor
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_expand_occupancy_logs_add_sensor_logs"
down_revision: Union[str, None] = "0002_add_seat_usage_factor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("occupancy_logs") as batch_op:
        batch_op.alter_column("analysis_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("source_type", sa.String(length=50), nullable=False, server_default="image_upload"))
        batch_op.add_column(sa.Column("image_path", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("annotated_image_path", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    op.drop_constraint("occupancy_logs_analysis_id_fkey", "occupancy_logs", type_="foreignkey")
    op.create_foreign_key(
        "occupancy_logs_analysis_id_fkey",
        "occupancy_logs",
        "analyses",
        ["analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_occupancy_logs_source_type"), "occupancy_logs", ["source_type"], unique=False)
    op.execute("UPDATE occupancy_logs SET source_type = 'image_upload' WHERE source_type IS NULL")
    op.alter_column("occupancy_logs", "source_type", server_default=None)
    op.alter_column("occupancy_logs", "created_at", server_default=None)

    op.create_table(
        "sensor_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("power_kw", sa.Float(), nullable=False),
        sa.Column("door_count", sa.Integer(), nullable=False),
        sa.Column("noise_level", sa.Float(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_logs_id"), "sensor_logs", ["id"], unique=False)
    op.create_index(op.f("ix_sensor_logs_facility_id"), "sensor_logs", ["facility_id"], unique=False)
    op.create_index(op.f("ix_sensor_logs_timestamp"), "sensor_logs", ["timestamp"], unique=False)
    op.create_index(op.f("ix_sensor_logs_source_type"), "sensor_logs", ["source_type"], unique=False)
    op.create_index("ix_sensor_logs_facility_timestamp", "sensor_logs", ["facility_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sensor_logs_facility_timestamp", table_name="sensor_logs")
    op.drop_table("sensor_logs")

    op.drop_index(op.f("ix_occupancy_logs_source_type"), table_name="occupancy_logs")
    op.drop_constraint("occupancy_logs_analysis_id_fkey", "occupancy_logs", type_="foreignkey")
    op.create_foreign_key(
        "occupancy_logs_analysis_id_fkey",
        "occupancy_logs",
        "analyses",
        ["analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )
    with op.batch_alter_table("occupancy_logs") as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("annotated_image_path")
        batch_op.drop_column("image_path")
        batch_op.drop_column("source_type")
        batch_op.drop_column("confidence")
        batch_op.alter_column("analysis_id", existing_type=sa.Integer(), nullable=False)
