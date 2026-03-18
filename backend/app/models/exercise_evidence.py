import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class ExerciseEvidence(SQLModel, table=True):
    __tablename__ = "exercise_evidences"
    __table_args__ = (
        UniqueConstraint("training_log_id", "exercise_id", name="uq_exercise_evidence_log_exercise"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    training_log_id: Optional[uuid.UUID] = Field(default=None, foreign_key="training_logs.id", index=True)
    exercise_id: Optional[str] = Field(default=None, index=True)
    exercise_name: str
    evidence_type: str = Field(default="exercise", index=True)
    nutrition_date: Optional[date] = Field(default=None, index=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    client_note: Optional[str] = None
    photo_urls: Optional[Any] = Field(default_factory=list, sa_column=Column(JSON))
    submitted_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    trainer_feedback: Optional[str] = None
    trainer_rating: Optional[str] = None  # "correct" | "improve"
    trainer_photo_urls: Optional[Any] = Field(default_factory=list, sa_column=Column(JSON))
    responded_at: Optional[datetime] = Field(default=None, index=True)
    client_viewed_at: Optional[datetime] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
