import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.photo import PhotoType


class PhotoResponse(BaseModel):
    id:          uuid.UUID
    client_id:   uuid.UUID
    uploaded_by: uuid.UUID
    type:        PhotoType
    url:         str
    notes:       Optional[str]
    taken_at:    date
    created_at:  datetime

    model_config = {"from_attributes": True}


class PhotoTimelineGroup(BaseModel):
    date:   date
    photos: list[PhotoResponse]


class PhotoTimelineResponse(BaseModel):
    type:   PhotoType
    groups: list[PhotoTimelineGroup]


class PhotoUploadUrlRequest(BaseModel):
    file_name:    str
    content_type: str
    file_size:    Optional[int] = None


class PhotoUploadUrlResponse(BaseModel):
    r2_key:     str
    upload_url: str
    expires_in: int


class PhotoRecordRequest(BaseModel):
    r2_key:   str
    type:     PhotoType
    notes:    Optional[str] = None
    taken_at: date
