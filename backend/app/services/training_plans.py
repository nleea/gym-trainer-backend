import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.training_plan import TrainingPlan
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.trainingPlansInterface import TrainingPlansRepositoryInterface
from app.schemas.training_plan import (
    AssignTrainingPlanRequest,
    TrainingPlanCreate,
    TrainingPlanUpdate,
)


class TrainingPlansService:
    def __init__(
        self,
        plans_repo: TrainingPlansRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.plans_repo = plans_repo
        self.clients_repo = clients_repo

    def _assert_trainer_owns_plan(self, plan: TrainingPlan, trainer: User) -> None:
        if plan.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_plans(self, trainer: User) -> List[TrainingPlan]:
        return await self.plans_repo.list_by_trainer(trainer.id)

    async def get_plan(self, plan_id: uuid.UUID, current_user: User) -> TrainingPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        if current_user.role == "trainer":
            self._assert_trainer_owns_plan(plan, current_user)
        else:
            client = await self.clients_repo.get_by_user_id(current_user.id)
            if not client or client.plan_id != plan.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return plan

    async def create_plan(self, data: TrainingPlanCreate, trainer: User) -> TrainingPlan:
        plan = TrainingPlan(
            trainer_id=trainer.id,
            name=data.name,
            weeks=data.weeks,
        )
        return await self.plans_repo.create(plan)

    async def update_plan(
        self, plan_id: uuid.UUID, data: TrainingPlanUpdate, trainer: User
    ) -> TrainingPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        return await self.plans_repo.update(plan, data.model_dump(exclude_none=True))

    async def assign_plan(
        self, plan_id: uuid.UUID, data: AssignTrainingPlanRequest, trainer: User
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

        update_data = {"plan_id": plan.id}
        if data.start_date:
            update_data["start_date"] = data.start_date

        await self.clients_repo.update(client, update_data)
        return {"detail": "Plan assigned successfully"}
    
