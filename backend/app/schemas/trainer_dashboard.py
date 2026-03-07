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


class TrainerReportsStats(BaseModel):
    activeClients: int
    avgAttendance: int
    totalWorkouts: int
    totalMeals: int
    prsThisWeek: int


class AttendanceDayItem(BaseModel):
    day: str
    attended: int
    missed: int


class AdherenceRankingItem(BaseModel):
    clientId: str
    clientName: str
    avatar: Optional[str] = None
    workouts: int
    plannedWorkouts: int
    meals: int
    adherencePct: int


class WeeklyProgressItem(BaseModel):
    clientId: str
    clientName: str
    avatar: Optional[str] = None
    completedWorkouts: int
    plannedWorkouts: int
    volumeKg: float
    prs: int
    streak: int


class GroupVolumeItem(BaseModel):
    week: str
    volume: float


class WellbeingMoodDistribution(BaseModel):
    great: int
    good: int
    neutral: int
    bad: int
    terrible: int


class WellbeingSnapshot(BaseModel):
    avgStress: float
    avgEnergy: float
    avgSleep: float
    moodDistribution: WellbeingMoodDistribution
    clientsWithCheckin: int
    clientsWithoutCheckin: int


class PRThisWeekItem(BaseModel):
    clientName: str
    exerciseName: str
    newWeight: float
    previousBest: float
    date: str


class AdherenceHistoryItem(BaseModel):
    month: str
    adherencePct: int


class TrainerReportsResponse(BaseModel):
    stats: TrainerReportsStats
    attendance: List[AttendanceDayItem]
    adherenceRanking: List[AdherenceRankingItem]
    weeklyProgress: List[WeeklyProgressItem]
    groupVolume: List[GroupVolumeItem]
    wellbeingSnapshot: WellbeingSnapshot
    prsThisWeek: List[PRThisWeekItem]
    adherenceHistory: List[AdherenceHistoryItem]
