"""Add compound unique constraints for deadlock prevention

Revision ID: 013
Revises: 012
Create Date: 2026-03-14
"""
from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_training_logs_client_date",
        "training_logs",
        ["client_id", "date"],
    )
    op.create_unique_constraint(
        "uq_meal_logs_client_date_meal_key",
        "meal_logs",
        ["client_id", "date", "meal_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_meal_logs_client_date_meal_key", "meal_logs", type_="unique")
    op.drop_constraint("uq_training_logs_client_date", "training_logs", type_="unique")
