import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    description: Optional[str] = None


class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    muscle_group: Optional[str] = None
    description: Optional[str] = None


class ExerciseResponse(BaseModel):
    id: uuid.UUID
    name: str
    muscle_group: Optional[str] = None
    description: Optional[str] = None
    trainer_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
