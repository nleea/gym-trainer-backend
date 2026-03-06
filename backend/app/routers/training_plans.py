import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_trainer
from app.dependencies import get_training_plans_service
from app.models.user import User
from app.schemas.training_plan import (
    AssignTrainingPlanRequest,
    TrainingPlanCreate,
    TrainingPlanResponse,
    TrainingPlanUpdate,
)
from app.services.training_plans import TrainingPlansService

router = APIRouter()


@router.get("", response_model=List[TrainingPlanResponse])
async def list_plans(
    trainer: User = Depends(require_trainer),
    service: TrainingPlansService = Depends(get_training_plans_service),
):
    return await service.list_plans(trainer)


@router.post("", response_model=TrainingPlanResponse, status_code=201)
async def create_plan(
    data: TrainingPlanCreate,
    trainer: User = Depends(require_trainer),
    service: TrainingPlansService = Depends(get_training_plans_service),
):
    return await service.create_plan(data, trainer)


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TrainingPlansService = Depends(get_training_plans_service),
):
    return await service.get_plan(plan_id, current_user)


@router.put("/{plan_id}", response_model=TrainingPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: TrainingPlanUpdate,
    trainer: User = Depends(require_trainer),
    service: TrainingPlansService = Depends(get_training_plans_service),
):
    return await service.update_plan(plan_id, data, trainer)


@router.post("/{plan_id}/assign")
async def assign_plan(
    plan_id: uuid.UUID,
    data: AssignTrainingPlanRequest,
    trainer: User = Depends(require_trainer),
    service: TrainingPlansService = Depends(get_training_plans_service),
):
    return await service.assign_plan(plan_id, data, trainer)
