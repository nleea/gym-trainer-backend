from pydantic import BaseModel


class LoggedExerciseItem(BaseModel):
    exercise_id: str
    exercise_name: str


class OneRepMaxItem(BaseModel):
    date: str              # 'YYYY-MM-DD'
    estimated_1rm: float


class ExerciseProgressItem(BaseModel):
    date: str              # 'YYYY-MM-DD'
    max_weight: float
    total_volume: float
