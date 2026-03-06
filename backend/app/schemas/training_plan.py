import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class TrainingPlanBase(BaseModel):
    name: str
    weeks: Optional[Any] = None  # JSON: list of week objects


class TrainingPlanCreate(TrainingPlanBase):
    pass


class TrainingPlanUpdate(BaseModel):
    name: Optional[str] = None
    weeks: Optional[Any] = None


class TrainingPlanResponse(TrainingPlanBase):
    id: uuid.UUID
    trainer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssignTrainingPlanRequest(BaseModel):
    client_id: uuid.UUID
    start_date: Optional[date] = None
