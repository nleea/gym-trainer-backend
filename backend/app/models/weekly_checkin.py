import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class WeeklyCheckin(SQLModel, table=True):
    __tablename__ = "weekly_checkins"
    __table_args__ = (
        UniqueConstraint("client_id", "week_start", name="uq_weekly_checkins_client_week"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    week_start: date = Field(index=True)

    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None    # 1-10
    stress_level: Optional[int] = None     # 1-10
    energy_level: Optional[int] = None     # 1-10
    muscle_soreness: Optional[int] = None  # 1-5
    mood: Optional[str] = None             # bad|regular|good|very_good|excellent
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
