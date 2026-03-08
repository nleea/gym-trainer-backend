"""Unify exercise and nutrition evidences in exercise_evidences table

Revision ID: 010
Revises: 009
Create Date: 2026-03-08 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exercise_evidences", sa.Column("evidence_type", sa.String(), nullable=True, server_default="exercise"))
    op.add_column("exercise_evidences", sa.Column("nutrition_date", sa.Date(), nullable=True))

    op.execute("UPDATE exercise_evidences SET evidence_type = 'exercise' WHERE evidence_type IS NULL")

    op.alter_column("exercise_evidences", "evidence_type", nullable=False, server_default=None)
    op.alter_column("exercise_evidences", "training_log_id", nullable=True)
    op.alter_column("exercise_evidences", "exercise_id", nullable=True)

    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('public.photos') IS NOT NULL THEN
            INSERT INTO exercise_evidences (
                id,
                training_log_id,
                exercise_id,
                exercise_name,
                evidence_type,
                nutrition_date,
                client_id,
                trainer_id,
                client_note,
                photo_urls,
                submitted_at,
                trainer_feedback,
                trainer_rating,
                trainer_photo_urls,
                responded_at,
                client_viewed_at,
                created_at
            )
            SELECT
                p.id,
                NULL,
                NULL,
                'Food evidence',
                'nutrition',
                p.taken_at,
                p.client_id,
                c.trainer_id,
                p.notes,
                json_build_array(p.r2_key),
                p.created_at,
                NULL,
                NULL,
                '[]'::json,
                NULL,
                NULL,
                p.created_at
            FROM photos p
            JOIN clients c ON c.id = p.client_id
            WHERE p.type = 'nutrition'
              AND NOT EXISTS (
                SELECT 1 FROM exercise_evidences e WHERE e.id = p.id
              );
          END IF;
        END $$;
        """
    )

    op.create_index("ix_exercise_evidences_evidence_type", "exercise_evidences", ["evidence_type"], unique=False)
    op.create_index("ix_exercise_evidences_nutrition_date", "exercise_evidences", ["nutrition_date"], unique=False)


def downgrade() -> None:
    op.execute("DELETE FROM exercise_evidences WHERE evidence_type = 'nutrition'")

    op.drop_index("ix_exercise_evidences_nutrition_date", table_name="exercise_evidences")
    op.drop_index("ix_exercise_evidences_evidence_type", table_name="exercise_evidences")

    op.alter_column("exercise_evidences", "exercise_id", nullable=False)
    op.alter_column("exercise_evidences", "training_log_id", nullable=False)

    op.drop_column("exercise_evidences", "nutrition_date")
    op.drop_column("exercise_evidences", "evidence_type")
