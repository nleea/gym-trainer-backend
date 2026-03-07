import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    external_id: Optional[str] = None
    name: str
    name_es: Optional[str] = None
    body_part: Optional[str] = None
    target: Optional[str] = None
    equipment: Optional[str] = None
    gif_url: Optional[str] = None
    secondary_muscles: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    synced_at: Optional[datetime] = None
    is_favorite: bool = False

    model_config = {"from_attributes": True}


class ExerciseListResponse(BaseModel):
    items: list[ExerciseResponse]
    total: int
    limit: int
    offset: int


class ExerciseFiltersResponse(BaseModel):
    body_parts: list[str]
    equipment: list[str]


class FavoriteExerciseResponse(BaseModel):
    user_id: uuid.UUID
    exercise_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ExerciseSyncResponse(BaseModel):
    synced_count: int
    updated_count: int
    created_count: int
    synced_at: datetime
