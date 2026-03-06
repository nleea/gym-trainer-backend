"""Add exercises table and notes/effort to training_logs

Revision ID: 002
Revises: 001
Create Date: 2026-03-04 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # exercises table
    op.create_table(
        "exercises",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("muscle_group", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "trainer_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_exercises_trainer_id", "exercises", ["trainer_id"])
    op.create_index("ix_exercises_name", "exercises", ["name"])

    # Add notes and effort to training_logs
    op.add_column("training_logs", sa.Column("notes", sa.Text, nullable=True))
    op.add_column("training_logs", sa.Column("effort", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("training_logs", "effort")
    op.drop_column("training_logs", "notes")
    op.drop_index("ix_exercises_name", table_name="exercises")
    op.drop_index("ix_exercises_trainer_id", table_name="exercises")
    op.drop_table("exercises")
