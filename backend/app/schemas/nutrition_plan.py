import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NutritionPlanBase(BaseModel):
    name: str
    days: Optional[Any] = None  # JSON: list of day objects
    target_calories: Optional[int] = None
    target_protein: Optional[int] = None
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None
    fiber_g: Optional[int] = None
    water_ml: Optional[int] = None
    meals_per_day: Optional[int] = None
    notes: Optional[str] = None


class NutritionPlanCreate(NutritionPlanBase):
    pass


class NutritionPlanUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[Any] = None
    target_calories: Optional[int] = None
    target_protein: Optional[int] = None
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None
    fiber_g: Optional[int] = None
    water_ml: Optional[int] = None
    meals_per_day: Optional[int] = None
    notes: Optional[str] = None


class NutritionPlanResponse(NutritionPlanBase):
    id: uuid.UUID
    trainer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssignNutritionPlanRequest(BaseModel):
    client_id: uuid.UUID
