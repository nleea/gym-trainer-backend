import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_daily_wellness_service
from app.models.user import User
from app.schemas.daily_wellness import DailyWellnessCreate, DailyWellnessResponse
from app.services.daily_wellness import DailyWellnessService

router = APIRouter()


@router.post("", response_model=DailyWellnessResponse, status_code=201)
async def create_wellness(
    data: DailyWellnessCreate,
    current_user: User = Depends(require_client),
    service: DailyWellnessService = Depends(get_daily_wellness_service),
):
    return await service.create_wellness(data, current_user)


@router.get("", response_model=List[DailyWellnessResponse])
async def list_wellness(
    client_id: uuid.UUID = Query(...),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    service: DailyWellnessService = Depends(get_daily_wellness_service),
):
    return await service.list_wellness(client_id, from_date, to_date, current_user)
