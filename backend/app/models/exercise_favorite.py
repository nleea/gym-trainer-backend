import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class ExerciseFavorite(SQLModel, table=True):
    __tablename__ = "exercise_favorites"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    exercise_id: uuid.UUID = Field(foreign_key="exercises.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
