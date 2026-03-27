"""Add lean_mass_kg to metrics and gender to clients

Revision ID: 015
Revises: 014
Create Date: 2026-03-25 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("metrics", sa.Column("lean_mass_kg", sa.Float(), nullable=True))
    op.add_column("clients", sa.Column("gender", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("clients", "gender")
    op.drop_column("metrics", "lean_mass_kg")
