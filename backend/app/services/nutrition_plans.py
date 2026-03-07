import uuid
import copy
from datetime import datetime, timezone
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

    async def list_templates(self, trainer: User) -> List[dict]:
        templates = await self.plans_repo.list_templates_by_trainer(trainer.id)
        result: list[dict] = []
        for tpl in templates:
            result.append({
                **tpl.model_dump(),
                "copies_count": await self.plans_repo.count_copies(tpl.id),
            })
        return result

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
            is_template=True,
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
        if plan.is_template:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usa el endpoint de plantillas para editar plantillas",
            )
        return await self.plans_repo.update(plan, data.model_dump(exclude_none=True))

    async def update_template(
        self, plan_id: uuid.UUID, data: NutritionPlanUpdate, trainer: User
    ) -> NutritionPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        if not plan.is_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usa el endpoint de cliente para planes asignados",
            )
        return await self.plans_repo.update(plan, data.model_dump(exclude_none=True))

    async def delete_template(self, plan_id: uuid.UUID, trainer: User) -> None:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        if not plan.is_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden eliminar plantillas",
            )

        await self.plans_repo.detach_template_from_copies(plan.id)
        await self.plans_repo.delete(plan)

    async def assign_plan(
        self, plan_id: uuid.UUID, data: AssignNutritionPlanRequest, trainer: User
    ) -> NutritionPlan:
        template = await self.plans_repo.get_by_id(plan_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(template, trainer)

        client = await self.clients_repo.get_by_id(data.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if client.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        new_plan = NutritionPlan(
            trainer_id=trainer.id,
            client_id=client.id,
            is_template=False,
            source_template_id=template.id,
            assigned_at=datetime.now(timezone.utc).replace(tzinfo=None),
            name=template.name,
            days=copy.deepcopy(template.days),
            target_calories=template.target_calories,
            target_protein=template.target_protein,
            target_carbs=template.target_carbs,
            target_fat=template.target_fat,
            fiber_g=template.fiber_g,
            water_ml=template.water_ml,
            meals_per_day=template.meals_per_day,
            notes=template.notes,
        )
        created_plan = await self.plans_repo.create(new_plan)

        await self.clients_repo.update(client, {"nutrition_plan_id": created_plan.id})
        return created_plan

    async def get_client_plan(self, client_id: uuid.UUID, current_user: User) -> NutritionPlan:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if current_user.role == "trainer":
            if client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own = await self.clients_repo.get_by_user_id(current_user.id)
            if not own or own.id != client.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        plan = await self.plans_repo.get_client_plan(client.id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan
