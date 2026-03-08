"""Add monthly_reports table

Revision ID: 011
Revises: 010
Create Date: 2026-03-08 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monthly_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("pdf_url", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("generated_by", sa.String(100), nullable=False, server_default="auto"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monthly_reports_client_id", "monthly_reports", ["client_id"])
    op.create_index("ix_monthly_reports_month", "monthly_reports", ["month"])


def downgrade() -> None:
    op.drop_index("ix_monthly_reports_month", table_name="monthly_reports")
    op.drop_index("ix_monthly_reports_client_id", table_name="monthly_reports")
    op.drop_table("monthly_reports")
