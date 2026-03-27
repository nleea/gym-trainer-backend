import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    status: Optional[str] = None
    start_date: Optional[date] = None
    goals: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class ClientCreate(ClientBase):
    # DECISION: When creating via /clients, a user_id must be provided
    # (the user was previously created via /auth/create-client)
    user_id: uuid.UUID


class ClientUpdate(BaseModel):
    status: Optional[str] = None
    start_date: Optional[date] = None
    goals: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    plan_id: Optional[uuid.UUID] = None
    nutrition_plan_id: Optional[uuid.UUID] = None


class ClientResponse(ClientBase):
    id: uuid.UUID
    user_id: uuid.UUID
    trainer_id: uuid.UUID
    plan_id: Optional[uuid.UUID] = None
    nutrition_plan_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientSummaryResponse(BaseModel):
    client: ClientResponse
    latest_metrics: Optional[Dict] = None
    attendance_last_30_days: int = 0
    attendance_total_last_30_days: int = 0
    recent_training_logs_count: int = 0
    recent_meal_logs_count: int = 0


class WorkoutSummaryStats(BaseModel):
    totalWorkouts: int = 0
    weeklyWorkouts: int = 0
    totalMinutes: int = 0
    currentStreak: int = 0


class ExerciseProgressItem(BaseModel):
    exerciseName: str
    bestWeight: float
    lastWeight: float
    lastDate: str
    trend: float


class WorkoutHistoryItem(BaseModel):
    id: str
    date: str
    duration: Optional[int] = None
    notes: Optional[str] = None
    effort: Optional[int] = None
    exercises: List[Any] = Field(default_factory=list)
    volume: float = 0.0
    maxWeight: float = 0.0


class WorkoutSummaryResponse(BaseModel):
    stats: WorkoutSummaryStats
    exerciseProgress: List[ExerciseProgressItem] = Field(default_factory=list)
    workoutHistory: List[WorkoutHistoryItem] = Field(default_factory=list)


class WeeklyVolumeItem(BaseModel):
    week: str
    volume: float


class HeatmapItem(BaseModel):
    date: str
    count: int
    volume: float
