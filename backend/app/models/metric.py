import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, JSON, Text
from sqlmodel import Field, SQLModel


class Metric(SQLModel, table=True):
    __tablename__ = "metrics"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    date: date

    # --- composición corporal ---
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_pct: Optional[float] = None
    water_pct: Optional[float] = None
    visceral_fat: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    bmr_kcal: Optional[float] = None
    lean_mass_kg: Optional[float] = None

    # --- legacy (kept for backwards compat) ---
    waist: Optional[float] = None
    arm: Optional[float] = None
    chest: Optional[float] = None

    # --- medidas torso (cm) ---
    neck_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    under_chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    abdomen_cm: Optional[float] = None
    hips_cm: Optional[float] = None

    # --- brazos (cm) ---
    arm_relaxed_left_cm: Optional[float] = None
    arm_relaxed_right_cm: Optional[float] = None
    arm_flexed_left_cm: Optional[float] = None
    arm_flexed_right_cm: Optional[float] = None
    forearm_left_cm: Optional[float] = None
    forearm_right_cm: Optional[float] = None

    # --- piernas (cm) ---
    thigh_left_cm: Optional[float] = None
    thigh_right_cm: Optional[float] = None
    calf_left_cm: Optional[float] = None
    calf_right_cm: Optional[float] = None

    # --- extra ---
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    photos: Optional[List] = Field(default=None, sa_column=Column(JSON))
    measurement_protocol: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
