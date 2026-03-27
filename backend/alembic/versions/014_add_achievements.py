"""Add achievements and client_achievements tables

Revision ID: 014
Revises: fe94bf80af0c
Create Date: 2026-03-25 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "014"
down_revision = "fe94bf80af0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("icon", sa.String(length=10), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_achievements_slug", "achievements", ["slug"], unique=True)
    op.create_index("ix_achievements_category", "achievements", ["category"])

    op.create_table(
        "client_achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("achievement_id", sa.UUID(), nullable=False),
        sa.Column("unlocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("unlocked_at", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "achievement_id", name="uq_client_achievement"),
    )
    op.create_index("ix_client_achievements_client_id", "client_achievements", ["client_id"])
    op.create_index("ix_client_achievements_achievement_id", "client_achievements", ["achievement_id"])

    # Seed default achievements
    op.execute("""
        INSERT INTO achievements (id, slug, title, description, icon, category, target) VALUES
        (gen_random_uuid(), 'first-workout',   'Primera sesión',     'Registra tu primer entrenamiento',    '🏋️', 'workouts', 1),
        (gen_random_uuid(), 'ten-workouts',    '10 sesiones',        'Completa 10 entrenamientos',          '💪', 'workouts', 10),
        (gen_random_uuid(), 'fifty-workouts',  '50 sesiones',        'Completa 50 entrenamientos',          '🔥', 'workouts', 50),
        (gen_random_uuid(), 'hundred-workouts','100 sesiones',       'Completa 100 entrenamientos',         '🏆', 'workouts', 100),
        (gen_random_uuid(), 'week-streak',     'Racha de 7 días',    'Entrena 7 días consecutivos',         '🔥', 'streaks',  7),
        (gen_random_uuid(), 'month-streak',    'Racha de 30 días',   'Entrena 30 días consecutivos',        '⚡', 'streaks',  30),
        (gen_random_uuid(), 'first-pr',        'Primer PR',          'Supera tu récord personal por primera vez', '🥇', 'strength', 1)
    """)


def downgrade() -> None:
    op.drop_index("ix_client_achievements_achievement_id", table_name="client_achievements")
    op.drop_index("ix_client_achievements_client_id", table_name="client_achievements")
    op.drop_table("client_achievements")
    op.drop_index("ix_achievements_category", table_name="achievements")
    op.drop_index("ix_achievements_slug", table_name="achievements")
    op.drop_table("achievements")
