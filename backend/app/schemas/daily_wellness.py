import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class DailyWellnessCreate(BaseModel):
    date: date
    energy: int
    sleep_quality: int
    muscle_fatigue: int
    notes: Optional[str] = None

    @field_validator("energy", "sleep_quality", "muscle_fatigue")
    @classmethod
    def validate_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Value must be between 1 and 5")
        return v


class DailyWellnessResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    date: date
    energy: int
    sleep_quality: int
    muscle_fatigue: int
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
