"""add job runs and extend alerts

Revision ID: 0005_add_job_runs_and_extend_alerts
Revises: 0004_add_operational_rollups
Create Date: 2026-05-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_job_runs_and_extend_alerts"
down_revision: Union[str, None] = "0004_add_operational_rollups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("facilities_processed", sa.Integer(), nullable=False),
        sa.Column("sensors_generated", sa.Integer(), nullable=False),
        sa.Column("rollups_computed", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_runs_id"), "job_runs", ["id"], unique=False)
    op.create_index(op.f("ix_job_runs_job_name"), "job_runs", ["job_name"], unique=False)
    op.create_index(op.f("ix_job_runs_status"), "job_runs", ["status"], unique=False)
    op.create_index(op.f("ix_job_runs_started_at"), "job_runs", ["started_at"], unique=False)
    op.create_index(op.f("ix_job_runs_finished_at"), "job_runs", ["finished_at"], unique=False)
    op.create_index(op.f("ix_job_runs_created_at"), "job_runs", ["created_at"], unique=False)

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("alert_type", sa.String(length=100), nullable=False, server_default="high_congestion"))
        batch_op.add_column(sa.Column("severity", sa.String(length=50), nullable=False, server_default="medium"))
        batch_op.add_column(sa.Column("title", sa.String(length=255), nullable=False, server_default="Operational alert"))
        batch_op.add_column(sa.Column("evidence_json", sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f("ix_alerts_alert_type"), ["alert_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_alerts_severity"), ["severity"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_index(batch_op.f("ix_alerts_severity"))
        batch_op.drop_index(batch_op.f("ix_alerts_alert_type"))
        batch_op.drop_column("evidence_json")
        batch_op.drop_column("title")
        batch_op.drop_column("severity")
        batch_op.drop_column("alert_type")

    op.drop_table("job_runs")
