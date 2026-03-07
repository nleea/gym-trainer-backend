"""Add exercise evidences table

Revision ID: 009
Revises: 008
Create Date: 2026-03-07 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exercise_evidences",
        sa.Column("id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("training_log_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("exercise_id", sa.String(), nullable=False),
        sa.Column("exercise_name", sa.String(), nullable=False),
        sa.Column("client_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("trainer_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("client_note", sa.String(), nullable=True),
        sa.Column("photo_urls", sa.JSON(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("trainer_feedback", sa.String(), nullable=True),
        sa.Column("trainer_rating", sa.String(), nullable=True),
        sa.Column("trainer_photo_urls", sa.JSON(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("client_viewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["training_log_id"], ["training_logs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("training_log_id", "exercise_id", name="uq_exercise_evidence_log_exercise"),
    )
    op.create_index("ix_exercise_evidences_training_log_id", "exercise_evidences", ["training_log_id"], unique=False)
    op.create_index("ix_exercise_evidences_exercise_id", "exercise_evidences", ["exercise_id"], unique=False)
    op.create_index("ix_exercise_evidences_client_id", "exercise_evidences", ["client_id"], unique=False)
    op.create_index("ix_exercise_evidences_trainer_id", "exercise_evidences", ["trainer_id"], unique=False)
    op.create_index("ix_exercise_evidences_submitted_at", "exercise_evidences", ["submitted_at"], unique=False)
    op.create_index("ix_exercise_evidences_responded_at", "exercise_evidences", ["responded_at"], unique=False)
    op.create_index("ix_exercise_evidences_client_viewed_at", "exercise_evidences", ["client_viewed_at"], unique=False)
    op.create_index("ix_exercise_evidences_created_at", "exercise_evidences", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_exercise_evidences_created_at", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_client_viewed_at", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_responded_at", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_submitted_at", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_trainer_id", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_client_id", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_exercise_id", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_training_log_id", table_name="exercise_evidences")
    op.drop_table("exercise_evidences")
