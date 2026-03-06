"""Add macro fields to nutrition_plans and meal_logs

Revision ID: 002
Revises: 001
Create Date: 2026-03-06 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── nutrition_plans: new macro / meta columns ─────────────────────────────
    op.add_column("nutrition_plans", sa.Column("target_protein", sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("target_carbs",   sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("target_fat",     sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("fiber_g",        sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("water_ml",       sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("meals_per_day",  sa.Integer, nullable=True))
    op.add_column("nutrition_plans", sa.Column("notes",          sa.Text,    nullable=True))

    # ── meal_logs: new fields for upsert / summary ────────────────────────────
    op.add_column("meal_logs", sa.Column("meal_name", sa.String(100), nullable=True))
    op.add_column("meal_logs", sa.Column("meal_key",  sa.String(100), nullable=True))
    op.add_column("meal_logs", sa.Column("carbs",     sa.Float,       nullable=True))
    op.add_column("meal_logs", sa.Column("fat",       sa.Float,       nullable=True))
    op.add_column("meal_logs", sa.Column("fiber",     sa.Float,       nullable=True))
    op.add_column("meal_logs", sa.Column("water_ml",  sa.Integer,     nullable=True))
    op.add_column("meal_logs", sa.Column("foods",     sa.JSON,        nullable=True))
    op.add_column("meal_logs", sa.Column("notes",     sa.Text,        nullable=True))

    # index meal_key for fast upsert lookups
    op.create_index("ix_meal_logs_meal_key", "meal_logs", ["meal_key"])


def downgrade() -> None:
    op.drop_index("ix_meal_logs_meal_key", table_name="meal_logs")

    op.drop_column("meal_logs", "notes")
    op.drop_column("meal_logs", "foods")
    op.drop_column("meal_logs", "water_ml")
    op.drop_column("meal_logs", "fiber")
    op.drop_column("meal_logs", "fat")
    op.drop_column("meal_logs", "carbs")
    op.drop_column("meal_logs", "meal_key")
    op.drop_column("meal_logs", "meal_name")

    op.drop_column("nutrition_plans", "notes")
    op.drop_column("nutrition_plans", "meals_per_day")
    op.drop_column("nutrition_plans", "water_ml")
    op.drop_column("nutrition_plans", "fiber_g")
    op.drop_column("nutrition_plans", "target_fat")
    op.drop_column("nutrition_plans", "target_carbs")
    op.drop_column("nutrition_plans", "target_protein")
