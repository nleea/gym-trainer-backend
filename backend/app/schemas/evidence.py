import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceItemResponse(BaseModel):
    id: uuid.UUID
    training_log_id: Optional[uuid.UUID] = None
    exercise_id: Optional[str] = None
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    type: str
    date: date
    exercise_name: str
    client_note: Optional[str] = None
    photo_urls: list[str] = Field(default_factory=list)
    submitted_at: datetime
    trainer_feedback: Optional[str] = None
    trainer_rating: Optional[str] = None
    trainer_photo_urls: list[str] = Field(default_factory=list)
    responded_at: Optional[datetime] = None
    client_viewed_at: Optional[datetime] = None
    created_at: datetime


class EvidenceDayResponse(BaseModel):
    date: date
    label: str
    evidences: list[EvidenceItemResponse]


class EvidenceWeekResponse(BaseModel):
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    days: list[EvidenceDayResponse]
