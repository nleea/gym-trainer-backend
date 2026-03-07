"""Add template/copy fields for training and nutrition plans

Revision ID: 008
Revises: 007
Create Date: 2026-03-07 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("training_plans", sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("training_plans", sa.Column("client_id", PGUUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True))
    op.add_column("training_plans", sa.Column("source_template_id", PGUUID(as_uuid=True), sa.ForeignKey("training_plans.id"), nullable=True))
    op.add_column("training_plans", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_training_plans_client_id", "training_plans", ["client_id"], unique=False)
    op.create_index("ix_training_plans_is_template", "training_plans", ["is_template"], unique=False)

    op.add_column("nutrition_plans", sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("nutrition_plans", sa.Column("client_id", PGUUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True))
    op.add_column("nutrition_plans", sa.Column("source_template_id", PGUUID(as_uuid=True), sa.ForeignKey("nutrition_plans.id"), nullable=True))
    op.add_column("nutrition_plans", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_nutrition_plans_client_id", "nutrition_plans", ["client_id"], unique=False)
    op.create_index("ix_nutrition_plans_is_template", "nutrition_plans", ["is_template"], unique=False)

    op.execute("UPDATE training_plans SET is_template = TRUE WHERE client_id IS NULL")
    op.execute("UPDATE nutrition_plans SET is_template = TRUE WHERE client_id IS NULL")

    op.alter_column("training_plans", "is_template", server_default=None)
    op.alter_column("nutrition_plans", "is_template", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_nutrition_plans_is_template", table_name="nutrition_plans")
    op.drop_index("ix_nutrition_plans_client_id", table_name="nutrition_plans")
    op.drop_column("nutrition_plans", "assigned_at")
    op.drop_column("nutrition_plans", "source_template_id")
    op.drop_column("nutrition_plans", "client_id")
    op.drop_column("nutrition_plans", "is_template")

    op.drop_index("ix_training_plans_is_template", table_name="training_plans")
    op.drop_index("ix_training_plans_client_id", table_name="training_plans")
    op.drop_column("training_plans", "assigned_at")
    op.drop_column("training_plans", "source_template_id")
    op.drop_column("training_plans", "client_id")
    op.drop_column("training_plans", "is_template")
