import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    muscle_group: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None)
    # null = exercise global/compartido; trainer_id = creado por ese trainer
    trainer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
