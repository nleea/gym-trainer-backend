import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    weeks: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
