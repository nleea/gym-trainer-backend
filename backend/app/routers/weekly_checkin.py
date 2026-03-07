import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_weekly_checkin_service
from app.models.user import User
from app.schemas.weekly_checkin import WeeklyCheckinCreate, WeeklyCheckinResponse, WeeklyCheckinUpdate
from app.services.weekly_checkin import WeeklyCheckinService

router = APIRouter()


@router.post("", response_model=WeeklyCheckinResponse, status_code=201)
async def upsert_checkin(
    data: WeeklyCheckinCreate,
    current_user: User = Depends(require_client),
    service: WeeklyCheckinService = Depends(get_weekly_checkin_service),
):
    return await service.upsert_checkin(data, current_user)


@router.get("/current", response_model=Optional[WeeklyCheckinResponse])
async def get_current_checkin(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    service: WeeklyCheckinService = Depends(get_weekly_checkin_service),
):
    return await service.get_current_checkin(client_id, current_user)


@router.get("", response_model=List[WeeklyCheckinResponse])
async def list_checkins(
    client_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    service: WeeklyCheckinService = Depends(get_weekly_checkin_service),
):
    return await service.list_checkins(client_id, current_user)


@router.put("/{checkin_id}", response_model=WeeklyCheckinResponse)
async def update_checkin(
    checkin_id: uuid.UUID,
    data: WeeklyCheckinUpdate,
    current_user: User = Depends(require_client),
    service: WeeklyCheckinService = Depends(get_weekly_checkin_service),
):
    return await service.update_checkin(checkin_id, data, current_user)
