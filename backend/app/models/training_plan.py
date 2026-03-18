import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel


class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    is_template: bool = Field(default=False, index=True)
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="clients.id", index=True)
    source_template_id: Optional[uuid.UUID] = Field(default=None, foreign_key="training_plans.id")
    assigned_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    name: str = Field(max_length=255)
    weeks: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
