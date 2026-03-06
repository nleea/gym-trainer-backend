import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class ProgressEntryBase(BaseModel):
    type: Optional[str] = None
    date: date
    weight: Optional[float] = None
    measurements: Optional[Any] = None  # JSON: dict of measurements
    photos: Optional[Any] = None        # JSON: list of photo paths
    notes: Optional[str] = None


class ProgressEntryCreate(ProgressEntryBase):
    pass


class ProgressEntryUpdate(BaseModel):
    type: Optional[str] = None
    weight: Optional[float] = None
    measurements: Optional[Any] = None
    photos: Optional[Any] = None
    notes: Optional[str] = None


class ProgressEntryResponse(ProgressEntryBase):
    id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
