import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class MealLog(SQLModel, table=True):
    __tablename__ = "meal_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    date: date
    type: str = Field(max_length=50)  # desayuno | almuerzo | cena | snack | water
    meal_name: Optional[str] = Field(default=None, max_length=100)
    meal_key: Optional[str] = Field(default=None, max_length=100, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    water_ml: Optional[int] = None
    foods: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
