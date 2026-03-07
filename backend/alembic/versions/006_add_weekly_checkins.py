"""Add weekly_checkins table

Revision ID: 006
Revises: 005
Create Date: 2026-03-06 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_checkins",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("trainer_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("week_start", sa.Date(), nullable=False, index=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("sleep_quality", sa.Integer(), nullable=True),
        sa.Column("stress_level", sa.Integer(), nullable=True),
        sa.Column("energy_level", sa.Integer(), nullable=True),
        sa.Column("muscle_soreness", sa.Integer(), nullable=True),
        sa.Column("mood", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_weekly_checkins_client_week",
        "weekly_checkins",
        ["client_id", "week_start"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_weekly_checkins_client_week", "weekly_checkins", type_="unique")
    op.drop_table("weekly_checkins")
