"""Add daily_wellness table

Revision ID: 016
Revises: 015
Create Date: 2026-03-26 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_wellness",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("energy", sa.Integer(), nullable=False),
        sa.Column("sleep_quality", sa.Integer(), nullable=False),
        sa.Column("muscle_fatigue", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "date", name="uq_wellness_client_date"),
    )
    op.create_index("ix_daily_wellness_client_id", "daily_wellness", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_daily_wellness_client_id", table_name="daily_wellness")
    op.drop_table("daily_wellness")
