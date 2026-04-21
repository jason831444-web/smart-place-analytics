"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_seats", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_facilities_id"), "facilities", ["id"], unique=False)
    op.create_index(op.f("ix_facilities_name"), "facilities", ["name"], unique=False)
    op.create_index(op.f("ix_facilities_type"), "facilities", ["type"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_facility_id"), "alerts", ["facility_id"], unique=False)
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)
    op.create_index(op.f("ix_alerts_triggered_at"), "alerts", ["triggered_at"], unique=False)

    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uploads_facility_id"), "uploads", ["facility_id"], unique=False)
    op.create_index(op.f("ix_uploads_id"), "uploads", ["id"], unique=False)
    op.create_index(op.f("ix_uploads_uploaded_at"), "uploads", ["uploaded_at"], unique=False)

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False),
        sa.Column("occupied_seats", sa.Integer(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column("occupancy_rate", sa.Float(), nullable=False),
        sa.Column("congestion_level", sa.String(length=50), nullable=False),
        sa.Column("congestion_score", sa.Float(), nullable=False),
        sa.Column("annotated_image_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_congestion_level"), "analyses", ["congestion_level"], unique=False)
    op.create_index(op.f("ix_analyses_created_at"), "analyses", ["created_at"], unique=False)
    op.create_index(op.f("ix_analyses_facility_id"), "analyses", ["facility_id"], unique=False)
    op.create_index(op.f("ix_analyses_id"), "analyses", ["id"], unique=False)
    op.create_index(op.f("ix_analyses_upload_id"), "analyses", ["upload_id"], unique=False)

    op.create_table(
        "occupancy_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False),
        sa.Column("occupied_seats", sa.Integer(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column("occupancy_rate", sa.Float(), nullable=False),
        sa.Column("congestion_score", sa.Float(), nullable=False),
        sa.Column("congestion_level", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_occupancy_logs_congestion_level"), "occupancy_logs", ["congestion_level"], unique=False)
    op.create_index(op.f("ix_occupancy_logs_facility_id"), "occupancy_logs", ["facility_id"], unique=False)
    op.create_index(op.f("ix_occupancy_logs_id"), "occupancy_logs", ["id"], unique=False)
    op.create_index(op.f("ix_occupancy_logs_timestamp"), "occupancy_logs", ["timestamp"], unique=False)
    op.create_index("ix_occupancy_logs_facility_timestamp", "occupancy_logs", ["facility_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_occupancy_logs_facility_timestamp", table_name="occupancy_logs")
    op.drop_table("occupancy_logs")
    op.drop_table("analyses")
    op.drop_table("uploads")
    op.drop_table("alerts")
    op.drop_table("facilities")
    op.drop_table("users")

