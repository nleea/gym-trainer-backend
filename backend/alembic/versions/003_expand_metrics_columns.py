"""Expand metrics table with full body measurement columns

Revision ID: 003
Revises: 002
Create Date: 2026-03-04 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("metrics", sa.Column("water_pct",            sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("visceral_fat",          sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("bone_mass_kg",          sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("bmr_kcal",              sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("neck_cm",               sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("shoulders_cm",          sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("chest_cm",              sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("under_chest_cm",        sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("waist_cm",              sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("abdomen_cm",            sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("hips_cm",               sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("arm_relaxed_left_cm",   sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("arm_relaxed_right_cm",  sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("arm_flexed_left_cm",    sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("arm_flexed_right_cm",   sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("forearm_left_cm",       sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("forearm_right_cm",      sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("thigh_left_cm",         sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("thigh_right_cm",        sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("calf_left_cm",          sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("calf_right_cm",         sa.Float, nullable=True))
    op.add_column("metrics", sa.Column("notes",                 sa.Text,  nullable=True))
    op.add_column("metrics", sa.Column("photos",                sa.JSON,  nullable=True))
    op.add_column("metrics", sa.Column("measurement_protocol",  sa.String(50), nullable=True))


def downgrade() -> None:
    for col in [
        "measurement_protocol", "photos", "notes",
        "calf_right_cm", "calf_left_cm", "thigh_right_cm", "thigh_left_cm",
        "forearm_right_cm", "forearm_left_cm",
        "arm_flexed_right_cm", "arm_flexed_left_cm",
        "arm_relaxed_right_cm", "arm_relaxed_left_cm",
        "hips_cm", "abdomen_cm", "waist_cm", "under_chest_cm",
        "chest_cm", "shoulders_cm", "neck_cm",
        "bmr_kcal", "bone_mass_kg", "visceral_fat", "water_pct",
    ]:
        op.drop_column("metrics", col)
