import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_meal_logs_service
from app.models.user import User
from app.schemas.meal_log import MealLogCreate, MealLogResponse, MealLogUpsert, NutritionSummaryResponse
from app.services.meal_logs import MealLogsService

router = APIRouter()


@router.get("", response_model=List[MealLogResponse])
async def list_logs(
    client_id: Optional[uuid.UUID] = Query(None),
    log_date: Optional[date] = Query(None, alias="date"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    service: MealLogsService = Depends(get_meal_logs_service),
):
    return await service.list_logs(current_user, client_id, log_date, start_date, end_date)


@router.post("", response_model=MealLogResponse, status_code=201)
async def create_log(
    data: MealLogCreate,
    current_user: User = Depends(require_client),
    service: MealLogsService = Depends(get_meal_logs_service),
):
    return await service.create_log(data, current_user)


@router.post("/upsert", response_model=MealLogResponse, status_code=200)
async def upsert_log(
    data: MealLogUpsert,
    current_user: User = Depends(require_client),
    service: MealLogsService = Depends(get_meal_logs_service),
):
    return await service.upsert_log(data, current_user)


@router.get("/nutrition-summary", response_model=NutritionSummaryResponse)
async def get_nutrition_summary(
    client_id: uuid.UUID = Query(...),
    summary_date: date = Query(..., alias="date"),
    current_user: User = Depends(get_current_user),
    service: MealLogsService = Depends(get_meal_logs_service),
):
    return await service.get_nutrition_summary(client_id, summary_date, current_user)


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: uuid.UUID,
    current_user: User = Depends(require_client),
    service: MealLogsService = Depends(get_meal_logs_service),
):
    await service.delete_log(log_id, current_user)
