import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel


class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    external_id: Optional[str] = Field(default=None, max_length=32, unique=True, index=True)
    name: str = Field(max_length=255, index=True)
    name_es: Optional[str] = Field(default=None, max_length=255)
    body_part: Optional[str] = Field(default=None, max_length=100, index=True)
    target: Optional[str] = Field(default=None, max_length=100)
    equipment: Optional[str] = Field(default=None, max_length=100, index=True)
    gif_url: Optional[str] = Field(default=None, max_length=1000)
    secondary_muscles: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    instructions: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    synced_at: Optional[datetime] = None

    # Campos legacy mantenidos por compatibilidad con flujos existentes.
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    trainer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
