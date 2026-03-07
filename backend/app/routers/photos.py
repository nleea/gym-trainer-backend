import uuid

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.dependencies import get_photo_service
from app.models.photo import PhotoType
from app.models.user import User
from app.schemas.photo import (
    PhotoRecordRequest,
    PhotoResponse,
    PhotoTimelineResponse,
    PhotoUploadUrlRequest,
    PhotoUploadUrlResponse,
)
from app.services.photo_service import PhotoService

router = APIRouter()


@router.post("/{client_id}/upload-url", response_model=PhotoUploadUrlResponse)
async def create_upload_url(
    client_id:    uuid.UUID,
    data:         PhotoUploadUrlRequest,
    current_user: User         = Depends(get_current_user),
    service:      PhotoService = Depends(get_photo_service),
):
    return await service.create_upload_url(
        client_id, current_user, data.file_name, data.content_type, data.file_size
    )


@router.post("/{client_id}/record", response_model=PhotoResponse, status_code=201)
async def save_photo_record(
    client_id:    uuid.UUID,
    data:         PhotoRecordRequest,
    current_user: User         = Depends(get_current_user),
    service:      PhotoService = Depends(get_photo_service),
):
    return await service.save_photo_record(
        client_id, current_user, data.r2_key, data.type, data.notes, data.taken_at
    )


@router.get("/{client_id}/timeline/{photo_type}", response_model=PhotoTimelineResponse)
async def get_timeline(
    client_id:    uuid.UUID,
    photo_type:   PhotoType,
    current_user: User         = Depends(get_current_user),
    service:      PhotoService = Depends(get_photo_service),
):
    return await service.get_timeline(client_id, photo_type, current_user)


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id:     uuid.UUID,
    current_user: User         = Depends(get_current_user),
    service:      PhotoService = Depends(get_photo_service),
):
    await service.delete_photo(photo_id, current_user)
