import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, field_validator


class SetLog(BaseModel):
    reps: int
    weight: float
    rpe: Optional[float] = None
    completed: bool = True


class ExerciseLog(BaseModel):
    exerciseId: str
    exerciseName: str
    sets: List[SetLog]
    notes: Optional[str] = None


def _normalize_exercise(raw: Any) -> dict:
    """
    Convierte cualquier formato viejo al esquema ExerciseLog.

    Formato viejo (guardado antes del schema tipado):
      {"name": "Press Banca", "sets": 4, "reps": 8, "weight": "56kg"}

    Formato nuevo:
      {"exerciseId": "...", "exerciseName": "...", "sets": [{reps, weight, completed}]}
    """
    if not isinstance(raw, dict):
        return raw

    # Ya tiene el formato nuevo
    if "exerciseName" in raw and isinstance(raw.get("sets"), list):
        return raw

    # Formato viejo: convierte
    name = raw.get("name") or raw.get("exerciseName") or ""
    exercise_id = raw.get("exerciseId") or raw.get("id") or name.lower().replace(" ", "_")

    # sets era un entero (número de series), reps y weight eran campos raíz
    sets_count = raw.get("sets") if isinstance(raw.get("sets"), int) else 1
    reps = int(raw.get("reps") or 0)
    # weight puede venir como "56kg" o como número
    weight_raw = raw.get("weight") or 0
    if isinstance(weight_raw, str):
        weight = float("".join(c for c in weight_raw if c.isdigit() or c == ".") or 0)
    else:
        weight = float(weight_raw)

    sets = [{"reps": reps, "weight": weight, "completed": True}] * max(sets_count, 1)

    return {
        "exerciseId": str(exercise_id),
        "exerciseName": name,
        "sets": sets,
        "notes": raw.get("notes"),
    }


class TrainingLogBase(BaseModel):
    date: date
    exercises: Optional[List[ExerciseLog]] = None
    duration: Optional[int] = None
    notes: Optional[str] = None
    effort: Optional[int] = None


class TrainingLogCreate(TrainingLogBase):
    pass


class TrainingLogUpdate(BaseModel):
    exercises: Optional[List[ExerciseLog]] = None
    duration: Optional[int] = None
    notes: Optional[str] = None
    effort: Optional[int] = None


class TrainingLogResponse(TrainingLogBase):
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("exercises", mode="before")
    @classmethod
    def normalize_exercises(cls, v: Any) -> Any:
        """Acepta tanto el formato viejo como el nuevo al leer de la DB."""
        if v is None:
            return v
        if not isinstance(v, list):
            return v
        return [_normalize_exercise(item) for item in v]


class PRItem(BaseModel):
    exerciseName: str
    newWeight: float
    previousBest: float


class TrainingLogWithPRsResponse(BaseModel):
    log: TrainingLogResponse
    prs: List[PRItem]


class LastPerformanceItem(BaseModel):
    exercise_id: str
    date: str
    reps: int
    weight: float
