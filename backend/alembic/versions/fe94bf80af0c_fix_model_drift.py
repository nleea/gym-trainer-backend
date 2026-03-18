"""fix-model-drift

Revision ID: fe94bf80af0c
Revises: 013
Create Date: 2026-03-17 20:56:27.496839
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'fe94bf80af0c'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(op.f('ix_attendance_trainer_id'), 'attendance', ['trainer_id'], unique=False)
    op.drop_index('ix_exercise_favorites_exercise_id', table_name='exercise_favorites')
    op.alter_column('meal_logs', 'type',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
    op.create_index(op.f('ix_training_logs_trainer_id'), 'training_logs', ['trainer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_training_logs_trainer_id'), table_name='training_logs')
    op.alter_column('meal_logs', 'type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.create_index('ix_exercise_favorites_exercise_id', 'exercise_favorites', ['exercise_id'], unique=False)
    op.drop_index(op.f('ix_attendance_trainer_id'), table_name='attendance')
