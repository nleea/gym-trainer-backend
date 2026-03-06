import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    date: date
    attended: bool = Field(default=False)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
