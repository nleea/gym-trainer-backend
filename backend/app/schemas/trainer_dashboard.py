from typing import List, Optional

from pydantic import BaseModel


class TrainerDashboardStats(BaseModel):
    totalClients: int
    activeThisWeek: int
    inactiveClients: int
    prsThisWeek: int


class LastCheckinSummary(BaseModel):
    mood: Optional[str]
    energy: Optional[int]
    stress: Optional[int]
    weekStart: str


class WeightPoint(BaseModel):
    date: str
    weightKg: Optional[float]


class RecentWorkoutItem(BaseModel):
    date: str
    exerciseCount: int
    volume: float
    duration: Optional[int]


class DashboardClientItem(BaseModel):
    id: str
    name: str
    avatar: None = None
    streak: int
    lastWorkout: Optional[str]
    daysSinceLastWorkout: Optional[int]
    weeklyWorkouts: int
    weightKg: Optional[float]
    weightChange: Optional[float]
    currentPlan: Optional[str]
    hasNutritionPlan: bool
    lastCheckin: Optional[LastCheckinSummary]
    alerts: List[str]
    workoutDates7d: List[str]       # YYYY-MM-DD dates this week for activity dots
    recentWorkouts: List[RecentWorkoutItem]
    weightHistory: List[WeightPoint]


class TrainerDashboardResponse(BaseModel):
    stats: TrainerDashboardStats
    clients: List[DashboardClientItem]
