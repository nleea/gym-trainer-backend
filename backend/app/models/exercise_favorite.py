import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class ExerciseFavorite(SQLModel, table=True):
    __tablename__ = "exercise_favorites"

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    )
    exercise_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
