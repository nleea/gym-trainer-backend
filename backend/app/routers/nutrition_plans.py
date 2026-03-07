import uuid
from typing import List

from fastapi import APIRouter, Depends, status

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


@router.get("/templates", response_model=List[NutritionPlanResponse])
async def list_templates(
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.list_templates(trainer)


@router.post("", response_model=NutritionPlanResponse, status_code=201)
async def create_plan(
    data: NutritionPlanCreate,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.create_plan(data, trainer)


@router.get("/client/{client_id}", response_model=NutritionPlanResponse)
async def get_client_plan(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.get_client_plan(client_id, current_user)


@router.get("/{plan_id}", response_model=NutritionPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.get_plan(plan_id, current_user)


@router.put("/templates/{plan_id}", response_model=NutritionPlanResponse)
async def update_template(
    plan_id: uuid.UUID,
    data: NutritionPlanUpdate,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.update_template(plan_id, data, trainer)


@router.put("/{plan_id}", response_model=NutritionPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: NutritionPlanUpdate,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.update_plan(plan_id, data, trainer)


@router.delete("/templates/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    plan_id: uuid.UUID,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    await service.delete_template(plan_id, trainer)
    return None


@router.post("/{plan_id}/assign", response_model=NutritionPlanResponse)
async def assign_plan(
    plan_id: uuid.UUID,
    data: AssignNutritionPlanRequest,
    trainer: User = Depends(require_trainer),
    service: NutritionPlansService = Depends(get_nutrition_plans_service),
):
    return await service.assign_plan(plan_id, data, trainer)
