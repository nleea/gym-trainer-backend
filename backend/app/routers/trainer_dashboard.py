from fastapi import APIRouter, Depends

from app.core.dependencies import require_trainer
from app.dependencies import get_trainer_dashboard_service
from app.models.user import User
from app.schemas.trainer_dashboard import TrainerDashboardResponse
from app.services.trainer_dashboard import TrainerDashboardService

router = APIRouter()


@router.get("/dashboard", response_model=TrainerDashboardResponse)
async def get_trainer_dashboard(
    trainer: User = Depends(require_trainer),
    service: TrainerDashboardService = Depends(get_trainer_dashboard_service),
):
    return await service.get_dashboard(trainer)
