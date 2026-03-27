import uuid
import copy
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import HTTPException, status

from app.models.exercise import Exercise
from app.models.training_plan import TrainingPlan
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface
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
        exercises_repo: Optional[ExercisesRepositoryInterface] = None,
    ) -> None:
        self.plans_repo = plans_repo
        self.clients_repo = clients_repo
        self.exercises_repo = exercises_repo

    def _assert_trainer_owns_plan(self, plan: TrainingPlan, trainer: User) -> None:
        if plan.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    @staticmethod
    def _extract_exercise_names(weeks: Any) -> List[str]:
        """Extract unique exercise names from the weeks JSON."""
        if not isinstance(weeks, list):
            return []
        names: set[str] = set()
        for week in weeks:
            if not isinstance(week, dict):
                continue
            for day in week.get("days") or []:
                if not isinstance(day, dict):
                    continue
                for ex in day.get("exercises") or []:
                    if not isinstance(ex, dict):
                        continue
                    name = (ex.get("name") or "").strip()
                    if name:
                        names.add(name)
        return list(names)

    async def _ensure_exercises_exist(self, weeks: Any, trainer: User) -> None:
        """Create Exercise records for any plan exercise not yet in the DB."""
        if not self.exercises_repo:
            return
        names = self._extract_exercise_names(weeks)
        if not names:
            return
        existing = await self.exercises_repo.find_existing_names(names)
        for name in names:
            if name.strip().lower() in existing:
                continue
            exercise = Exercise(name=name, trainer_id=trainer.id)
            await self.exercises_repo.create(exercise)

    async def list_plans(self, trainer: User) -> List[TrainingPlan]:
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
            is_template=True,
            name=data.name,
            weeks=data.weeks,
        )
        created = await self.plans_repo.create(plan)
        await self._ensure_exercises_exist(data.weeks, trainer)
        return created

    async def update_plan(
        self, plan_id: uuid.UUID, data: TrainingPlanUpdate, trainer: User
    ) -> TrainingPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        if plan.is_template:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usa el endpoint de plantillas para editar plantillas",
            )
        updated = await self.plans_repo.update(plan, data.model_dump(exclude_none=True))
        if data.weeks is not None:
            await self._ensure_exercises_exist(data.weeks, trainer)
        return updated

    async def update_template(
        self, plan_id: uuid.UUID, data: TrainingPlanUpdate, trainer: User
    ) -> TrainingPlan:
        plan = await self.plans_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(plan, trainer)
        if not plan.is_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usa el endpoint de cliente para planes asignados",
            )
        updated = await self.plans_repo.update(plan, data.model_dump(exclude_none=True))
        if data.weeks is not None:
            await self._ensure_exercises_exist(data.weeks, trainer)
        return updated

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
        self, plan_id: uuid.UUID, data: AssignTrainingPlanRequest, trainer: User
    ) -> TrainingPlan:
        template = await self.plans_repo.get_by_id(plan_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        self._assert_trainer_owns_plan(template, trainer)

        client = await self.clients_repo.get_by_id(data.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if client.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        new_plan = TrainingPlan(
            trainer_id=trainer.id,
            client_id=client.id,
            is_template=False,
            source_template_id=template.id,
            assigned_at=datetime.now(timezone.utc).replace(tzinfo=None),
            name=template.name,
            weeks=copy.deepcopy(template.weeks),
        )
        created_plan = await self.plans_repo.create(new_plan)

        update_data = {"plan_id": created_plan.id}
        if data.start_date:
            update_data["start_date"] = data.start_date

        await self.clients_repo.update(client, update_data)
        return created_plan

    async def get_client_plan(self, client_id: uuid.UUID, current_user: User) -> TrainingPlan:
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
