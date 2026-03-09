from typing import Literal

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import require_trainer
from app.dependencies import get_trainer_dashboard_service
from app.models.user import User
from app.schemas.trainer_dashboard import TrainerDashboardResponse
from app.schemas.trainer_dashboard import TrainerReportsResponse
from app.services.trainer_dashboard import TrainerDashboardService

router = APIRouter()


@router.get("/dashboard", response_model=TrainerDashboardResponse)
async def get_trainer_dashboard(
    request: Request,
    trainer: User = Depends(require_trainer),
    service: TrainerDashboardService = Depends(get_trainer_dashboard_service),
):
    timezone_name = request.headers.get("X-Timezone")
    return await service.get_dashboard(trainer, timezone_name=timezone_name)


@router.get("/{trainer_id}/reports", response_model=TrainerReportsResponse)
async def get_trainer_reports(
    trainer_id: str,
    request: Request,
    period: Literal["week", "month"] = Query("week"),
    trainer: User = Depends(require_trainer),
    service: TrainerDashboardService = Depends(get_trainer_dashboard_service),
):
    timezone_name = request.headers.get("X-Timezone")
    return await service.get_reports(
        trainer,
        trainer_id=trainer_id,
        period=period,
        timezone_name=timezone_name,
    )
