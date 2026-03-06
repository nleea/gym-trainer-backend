import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # DECISION: user_id added to link client profile to the user account for authentication
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    trainer_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    status: Optional[str] = Field(default=None, max_length=50)
    start_date: Optional[date] = None
    goals: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    plan_id: Optional[uuid.UUID] = Field(default=None, foreign_key="training_plans.id")
    nutrition_plan_id: Optional[uuid.UUID] = Field(default=None, foreign_key="nutrition_plans.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
