from typing import List, Optional

from pydantic import BaseModel


class WeeklyVolume(BaseModel):
    week: str  # 'YYYY-MM-DD' (Monday of the week)
    volume: float  # sum of sets × reps × weight


class VolumeResponse(BaseModel):
    weeks: List[WeeklyVolume]
    total_volume: float


class AdherenceBlock(BaseModel):
    completed: int
    planned: int
    percentage: float


class AdherenceResponse(BaseModel):
    training: AdherenceBlock
    nutrition: AdherenceBlock
