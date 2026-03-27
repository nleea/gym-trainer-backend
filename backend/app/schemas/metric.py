import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetricBase(BaseModel):
    date: date

    # composición
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_pct: Optional[float] = None
    water_pct: Optional[float] = None
    visceral_fat: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    bmr_kcal: Optional[float] = None
    lean_mass_kg: Optional[float] = None

    # legacy
    waist: Optional[float] = None
    arm: Optional[float] = None
    chest: Optional[float] = None

    # medidas torso (cm)
    neck_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    under_chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    abdomen_cm: Optional[float] = None
    hips_cm: Optional[float] = None

    # brazos (cm)
    arm_relaxed_left_cm: Optional[float] = None
    arm_relaxed_right_cm: Optional[float] = None
    arm_flexed_left_cm: Optional[float] = None
    arm_flexed_right_cm: Optional[float] = None
    forearm_left_cm: Optional[float] = None
    forearm_right_cm: Optional[float] = None

    # piernas (cm)
    thigh_left_cm: Optional[float] = None
    thigh_right_cm: Optional[float] = None
    calf_left_cm: Optional[float] = None
    calf_right_cm: Optional[float] = None

    notes: Optional[str] = None
    photos: Optional[List[Any]] = None
    measurement_protocol: Optional[str] = None


class MetricCreate(MetricBase):
    pass


class MetricUpdate(BaseModel):
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_pct: Optional[float] = None
    water_pct: Optional[float] = None
    visceral_fat: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    bmr_kcal: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    waist: Optional[float] = None
    arm: Optional[float] = None
    chest: Optional[float] = None
    neck_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    under_chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    abdomen_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    arm_relaxed_left_cm: Optional[float] = None
    arm_relaxed_right_cm: Optional[float] = None
    arm_flexed_left_cm: Optional[float] = None
    arm_flexed_right_cm: Optional[float] = None
    forearm_left_cm: Optional[float] = None
    forearm_right_cm: Optional[float] = None
    thigh_left_cm: Optional[float] = None
    thigh_right_cm: Optional[float] = None
    calf_left_cm: Optional[float] = None
    calf_right_cm: Optional[float] = None
    notes: Optional[str] = None
    photos: Optional[List[Any]] = None
    measurement_protocol: Optional[str] = None


class MetricResponse(MetricBase):
    id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Metrics Summary ─────────────────────────────────────────────────────────

class DeltaValue(BaseModel):
    lastValue: Optional[float] = None
    change: Optional[float] = None


class SeriesPoint(BaseModel):
    date: str
    value: float


class MetricsSummaryResponse(BaseModel):
    deltas: Dict[str, DeltaValue]
    series: Dict[str, List[SeriesPoint]]
    history: List[MetricResponse]


class BodyCompositionPoint(BaseModel):
    date: str
    body_fat_pct: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    weight_kg: Optional[float] = None


class BodyCompositionResponse(BaseModel):
    points: List[BodyCompositionPoint]


class MetricPhotoUploadRequest(BaseModel):
    file_name: str
    content_type: str
    file_size: Optional[int] = None


class MetricPhotoUploadResponse(BaseModel):
    key: str
    upload_url: str
    public_url: str
    expires_in: int
