import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Achievement(SQLModel, table=True):
    __tablename__ = "achievements"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    slug: str = Field(max_length=100, unique=True, index=True)
    title: str = Field(max_length=255)
    description: str = Field(max_length=500)
    icon: str = Field(max_length=10)
    category: str = Field(max_length=50, index=True)
    target: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClientAchievement(SQLModel, table=True):
    __tablename__ = "client_achievements"
    __table_args__ = (
        UniqueConstraint("client_id", "achievement_id", name="uq_client_achievement"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    achievement_id: uuid.UUID = Field(foreign_key="achievements.id", index=True)
    unlocked: bool = Field(default=False)
    unlocked_at: Optional[datetime] = Field(default=None)
    progress: int = Field(default=0)
