import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.nutrition_plan import NutritionPlan
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.nutritionPlansInterface import NutritionPlansRepositoryInterface
from app.schemas.nutrition_plan import (
    AssignNutritionPlanRequest,
    NutritionPlanCreate,
    NutritionPlanUpdate,
)


class NutritionPlansService:
    def __init__(
        self,
        plans_repo: NutritionPlansRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.plans_repo = plans_repo
        self.clients_repo = clients_repo

    def _assert_trainer_owns_plan(self, plan: NutritionPlan, trainer: User) -> None:
        if plan.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_plans(self, trainer: User) -> List[NutritionPlan]:
        return await self.plans_repo.list_by_trainer(trainer.id)

    async def get_plan(self, plan_id: uuid.UUID, current_user: User) -> NutritionPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        if current_user.role == "trainer":
            self._assert_trainer_owns_plan(plan, current_user)
        else:
            client = await self.clients_repo.get_by_user_id(current_user.id)
            if not client or client.nutrition_plan_id != plan.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return plan

    async def create_plan(self, data: NutritionPlanCreate, trainer: User) -> NutritionPlan:
        plan = NutritionPlan(
            trainer_id=trainer.id,
            name=data.name,
            days=data.days,
            target_calories=data.target_calories,
            target_protein=data.target_protein,
            target_carbs=data.target_carbs,
            target_fat=data.target_fat,
            fiber_g=data.fiber_g,
            water_ml=data.water_ml,
            meals_per_day=data.meals_per_day,
            notes=data.notes,
        )
        return await self.plans_repo.create(plan)

    async def update_plan(
        self, plan_id: uuid.UUID, data: NutritionPlanUpdate, trainer: User
    ) -> NutritionPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        return await self.plans_repo.update(plan, data.model_dump(exclude_none=True))

    async def assign_plan(
        self, plan_id: uuid.UUID, data: AssignNutritionPlanRequest, trainer: User
    ) -> dict:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)

        client = await self.clients_repo.get_by_id(data.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if client.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await self.clients_repo.update(client, {"nutrition_plan_id": plan.id})
        return {"detail": "Nutrition plan assigned successfully"}
