import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class AttendanceBase(BaseModel):
    date: date
    attended: bool = False
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    client_id: uuid.UUID


class AttendanceUpdate(BaseModel):
    attended: Optional[bool] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
