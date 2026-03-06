import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class MealLogBase(BaseModel):
    date: date
    type: str  # desayuno | almuerzo | cena | snack | water
    meal_name: Optional[str] = None
    meal_key: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    water_ml: Optional[int] = None
    foods: Optional[Any] = None
    notes: Optional[str] = None


class MealLogCreate(MealLogBase):
    pass


class MealLogUpsert(MealLogBase):
    """Used for the upsert endpoint — finds existing by client+date+meal_key and updates, or creates."""
    pass


class MealLogUpdate(BaseModel):
    type: Optional[str] = None
    meal_name: Optional[str] = None
    meal_key: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    water_ml: Optional[int] = None
    foods: Optional[Any] = None
    notes: Optional[str] = None


class MealLogResponse(MealLogBase):
    id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Nutrition summary ─────────────────────────────────────────────────────────

class MacroProgress(BaseModel):
    consumed: float
    target: float


class TodayMacros(BaseModel):
    calories: MacroProgress
    protein_g: MacroProgress
    carbs_g: MacroProgress
    fat_g: MacroProgress
    water_ml: MacroProgress


class Adherence(BaseModel):
    last_7_days: int
    last_30_days: int
    percentage: int


class DailyAdherence(BaseModel):
    date: str
    has_log: bool
    calories_pct: float


class NutritionSummaryResponse(BaseModel):
    today_logs: List[MealLogResponse]
    today_macros: TodayMacros
    adherence: Adherence
    daily_history: List[DailyAdherence]
