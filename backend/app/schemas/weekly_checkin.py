import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class WeeklyCheckinCreate(BaseModel):
    week_start: date
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    energy_level: Optional[int] = None
    muscle_soreness: Optional[int] = None
    mood: Optional[str] = None
    notes: Optional[str] = None


class WeeklyCheckinUpdate(BaseModel):
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    energy_level: Optional[int] = None
    muscle_soreness: Optional[int] = None
    mood: Optional[str] = None
    notes: Optional[str] = None


class WeeklyCheckinResponse(WeeklyCheckinCreate):
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
