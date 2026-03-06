import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_trainer
from app.dependencies import get_nutrition_plans_service
from app.models.user import User
from app.schemas.nutrition_plan import (
    AssignNutritionPlanRequest,
    NutritionPlanCreate,
    NutritionPlanResponse,
    NutritionPlanUpdate,
)
from app.services.nutrition_plans import NutritionPlansService

router = APIRouter()


@router.get("", response_model=List[NutritionPlanResponse])
async def list_plans(
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.list_plans(trainer)


@router.post("", response_model=NutritionPlanResponse, status_code=201)
async def create_plan(
    data: NutritionPlanCreate,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.create_plan(data, trainer)


@router.get("/{plan_id}", response_model=NutritionPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.get_plan(plan_id, current_user)


@router.put("/{plan_id}", response_model=NutritionPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: NutritionPlanUpdate,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.update_plan(plan_id, data, trainer)


@router.post("/{plan_id}/assign")
async def assign_plan(
    plan_id: uuid.UUID,
    data: AssignNutritionPlanRequest,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.assign_plan(plan_id, data, trainer)
