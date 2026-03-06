import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ProgressEntry(SQLModel, table=True):
    __tablename__ = "progress_entries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    type: Optional[str] = Field(default=None, max_length=50)
    date: date
    weight: Optional[float] = None
    measurements: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    # DECISION: photos stores file paths/URLs only; actual upload to R2 not implemented
    photos: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
