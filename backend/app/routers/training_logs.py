import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_training_logs_service
from app.models.user import User
from app.schemas.training_log import (
    TrainingLogCreate, TrainingLogResponse, TrainingLogUpdate,
    TrainingLogWithPRsResponse, LastPerformanceItem,
)
from app.services.training_logs import TrainingLogsService

router = APIRouter()


@router.get("", response_model=List[TrainingLogResponse])
async def list_logs(
    client_id: Optional[uuid.UUID] = Query(None),
    week_start: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    service: TrainingLogsService = Depends(get_training_logs_service),
):
    return await service.list_logs(current_user, client_id, week_start)


@router.post("", response_model=TrainingLogWithPRsResponse, status_code=201)
async def create_log(
    data: TrainingLogCreate,
    current_user: User = Depends(require_client),
    service: TrainingLogsService = Depends(get_training_logs_service),
):
    return await service.create_or_upsert_log(data, current_user)


@router.put("/{log_id}", response_model=TrainingLogResponse)
async def update_log(
    log_id: uuid.UUID,
    data: TrainingLogUpdate,
    current_user: User = Depends(require_client),
    service: TrainingLogsService = Depends(get_training_logs_service),
):
    return await service.update_log(log_id, data, current_user)


@router.get("/clients/{client_id}/last-performance", response_model=List[LastPerformanceItem])
async def get_last_performance(
    client_id: uuid.UUID,
    exercise_ids: str = Query(..., description="Comma-separated exercise IDs"),
    current_user: User = Depends(get_current_user),
    service: TrainingLogsService = Depends(get_training_logs_service),
):
    ids = [i.strip() for i in exercise_ids.split(",") if i.strip()]
    return await service.get_last_performance(client_id, ids, current_user)


@router.get("/{client_id}/week/{week_start}", response_model=List[TrainingLogResponse])
async def get_week_logs(
    client_id: uuid.UUID,
    week_start: date,
    current_user: User = Depends(get_current_user),
    service: TrainingLogsService = Depends(get_training_logs_service),
):
    return await service.get_week_logs(client_id, week_start, current_user)
