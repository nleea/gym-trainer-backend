import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class DailyWellness(SQLModel, table=True):
    __tablename__ = "daily_wellness"
    __table_args__ = (
        UniqueConstraint("client_id", "date", name="uq_wellness_client_date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    date: date
    energy: int
    sleep_quality: int
    muscle_fatigue: int
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
