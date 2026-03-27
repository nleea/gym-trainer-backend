from pydantic import BaseModel


class StreakResponse(BaseModel):
    current: int         # current consecutive-day streak
    best: int            # all-time best streak
    last_activity: str   # 'YYYY-MM-DD' or "" if no workouts
