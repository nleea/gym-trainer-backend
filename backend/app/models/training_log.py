import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class TrainingLog(SQLModel, table=True):
    __tablename__ = "training_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    date: date
    exercises: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    duration: Optional[int] = None  # minutes
    notes: Optional[str] = None
    effort: Optional[int] = None    # 1-10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
