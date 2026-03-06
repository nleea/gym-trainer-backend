"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-03-03 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # training_plans
    op.create_table(
        "training_plans",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("weeks", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_training_plans_trainer_id", "training_plans", ["trainer_id"])

    # nutrition_plans
    op.create_table(
        "nutrition_plans",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("days", sa.JSON, nullable=True),
        sa.Column("target_calories", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_nutrition_plans_trainer_id", "nutrition_plans", ["trainer_id"])

    # clients
    op.create_table(
        "clients",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("goals", sa.Text, nullable=True),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("height", sa.Float, nullable=True),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column(
            "plan_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("training_plans.id"),
            nullable=True,
        ),
        sa.Column(
            "nutrition_plan_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("nutrition_plans.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_clients_user_id", "clients", ["user_id"], unique=True)
    op.create_index("ix_clients_trainer_id", "clients", ["trainer_id"])

    # training_logs
    op.create_table(
        "training_logs",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("exercises", sa.JSON, nullable=True),
        sa.Column("duration", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_training_logs_client_id", "training_logs", ["client_id"])

    # meal_logs
    op.create_table(
        "meal_logs",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("calories", sa.Integer, nullable=True),
        sa.Column("protein", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_meal_logs_client_id", "meal_logs", ["client_id"])

    # progress_entries
    op.create_table(
        "progress_entries",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("measurements", sa.JSON, nullable=True),
        sa.Column("photos", sa.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_progress_entries_client_id", "progress_entries", ["client_id"])

    # attendance
    op.create_table(
        "attendance",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("attended", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_attendance_client_id", "attendance", ["client_id"])

    # metrics
    op.create_table(
        "metrics",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("body_fat_pct", sa.Float, nullable=True),
        sa.Column("muscle_pct", sa.Float, nullable=True),
        sa.Column("waist", sa.Float, nullable=True),
        sa.Column("arm", sa.Float, nullable=True),
        sa.Column("chest", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_metrics_client_id", "metrics", ["client_id"])


def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("attendance")
    op.drop_table("progress_entries")
    op.drop_table("meal_logs")
    op.drop_table("training_logs")
    op.drop_table("clients")
    op.drop_table("nutrition_plans")
    op.drop_table("training_plans")
    op.drop_table("users")
