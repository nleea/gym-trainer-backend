import uuid
from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


TrainerRating = Literal["correct", "improve"]


class ExerciseEvidenceFeedbackBody(BaseModel):
    trainer_feedback: Optional[str] = None
    trainer_rating: Optional[TrainerRating] = None
    trainer_photo_urls: Optional[List[str]] = None


class ExerciseEvidenceResponse(BaseModel):
    id: uuid.UUID
    training_log_id: uuid.UUID
    exercise_id: str
    exercise_name: str
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    client_note: Optional[str] = None
    photo_urls: List[str] = Field(default_factory=list)
    submitted_at: datetime
    trainer_feedback: Optional[str] = None
    trainer_rating: Optional[TrainerRating] = None
    trainer_photo_urls: List[str] = Field(default_factory=list)
    responded_at: Optional[datetime] = None
    client_viewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
