import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class PhotoType(str, Enum):
    progress  = "progress"
    profile   = "profile"
    nutrition = "nutrition"
    training  = "training"


class Photo(SQLModel, table=True):
    __tablename__ = "photos"

    id:          uuid.UUID     = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id:   uuid.UUID     = Field(foreign_key="clients.id", index=True)
    uploaded_by: uuid.UUID     = Field(index=True)
    type:        PhotoType     = Field(index=True)
    r2_key:      str           = Field()
    notes:       Optional[str] = Field(default=None)
    taken_at:    date          = Field()
    created_at:  datetime      = Field(default_factory=datetime.utcnow)
