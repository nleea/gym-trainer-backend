from typing import List, Optional

from pydantic import BaseModel


class TodayWellnessEntry(BaseModel):
    energy: int
    sleep_quality: int
    muscle_fatigue: int


class WellnessSummaryResponse(BaseModel):
    overload_alert: bool
    avg_fatigue_7d: float
    avg_energy_7d: float
    readiness_score: Optional[float] = None
    today_entry: Optional[TodayWellnessEntry] = None


class WellnessCorrelationPoint(BaseModel):
    week: str           # 'YYYY-MM-DD' (Monday)
    avg_fatigue: float
    volume: float


class WellnessCorrelationResponse(BaseModel):
    points: List[WellnessCorrelationPoint]
