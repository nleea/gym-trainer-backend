import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class NutritionPlan(SQLModel, table=True):
    __tablename__ = "nutrition_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    days: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    target_calories: Optional[int] = None
    target_protein: Optional[int] = None
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None
    fiber_g: Optional[int] = None
    water_ml: Optional[int] = None
    meals_per_day: Optional[int] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
