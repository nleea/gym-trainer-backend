import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_progress_service
from app.models.user import User
from app.schemas.progress_entry import ProgressEntryCreate, ProgressEntryResponse
from app.services.progress import ProgressService

router = APIRouter()


@router.get("/{client_id}", response_model=List[ProgressEntryResponse])
async def list_entries(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    return await service.list_entries(client_id, current_user)


@router.post("", response_model=ProgressEntryResponse, status_code=201)
async def create_entry(
    data: ProgressEntryCreate,
    current_user: User = Depends(require_client),
    service: ProgressService = Depends(get_progress_service),
):
    return await service.create_entry(data, current_user)
