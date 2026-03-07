"""Exercise library cache fields and favorites table

Revision ID: 007
Revises: 006
Create Date: 2026-03-07 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("external_id", sa.String(length=32), nullable=True))
    op.add_column("exercises", sa.Column("name_es", sa.String(length=255), nullable=True))
    op.add_column("exercises", sa.Column("body_part", sa.String(length=100), nullable=True))
    op.add_column("exercises", sa.Column("target", sa.String(length=100), nullable=True))
    op.add_column("exercises", sa.Column("equipment", sa.String(length=100), nullable=True))
    op.add_column("exercises", sa.Column("gif_url", sa.String(length=1000), nullable=True))
    op.add_column("exercises", sa.Column("secondary_muscles", sa.JSON(), nullable=True))
    op.add_column("exercises", sa.Column("instructions", sa.JSON(), nullable=True))
    op.add_column("exercises", sa.Column("synced_at", sa.DateTime(), nullable=True))

    op.create_index("ix_exercises_external_id", "exercises", ["external_id"], unique=True)
    op.create_index("ix_exercises_body_part", "exercises", ["body_part"], unique=False)
    op.create_index("ix_exercises_equipment", "exercises", ["equipment"], unique=False)

    op.create_table(
        "exercise_favorites",
        sa.Column(
            "user_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "exercise_id"),
    )
    op.create_index(
        "ix_exercise_favorites_exercise_id", "exercise_favorites", ["exercise_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_exercise_favorites_exercise_id", table_name="exercise_favorites")
    op.drop_table("exercise_favorites")

    op.drop_index("ix_exercises_equipment", table_name="exercises")
    op.drop_index("ix_exercises_body_part", table_name="exercises")
    op.drop_index("ix_exercises_external_id", table_name="exercises")

    op.drop_column("exercises", "synced_at")
    op.drop_column("exercises", "instructions")
    op.drop_column("exercises", "secondary_muscles")
    op.drop_column("exercises", "gif_url")
    op.drop_column("exercises", "equipment")
    op.drop_column("exercises", "target")
    op.drop_column("exercises", "body_part")
    op.drop_column("exercises", "name_es")
    op.drop_column("exercises", "external_id")
