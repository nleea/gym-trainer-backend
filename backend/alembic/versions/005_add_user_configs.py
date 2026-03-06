"""Add user_configs table

Revision ID: 005
Revises: 004
Create Date: 2026-03-06 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_configs",
        sa.Column("id",      sa.Integer,     primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(),     nullable=False),
        sa.Column("config",  sa.JSON,         nullable=False, server_default="{}"),
    )
    op.create_index("ix_user_configs_user_id", "user_configs", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_configs_user_id", table_name="user_configs")
    op.drop_table("user_configs")
