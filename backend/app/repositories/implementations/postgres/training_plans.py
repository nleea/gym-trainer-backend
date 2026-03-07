import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select
from sqlalchemy import update

from app.models.training_plan import TrainingPlan
from app.repositories.interface.trainingPlansInterface import TrainingPlansRepositoryInterface


class TrainingPlansRepository(TrainingPlansRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_trainer(self, trainer_id: uuid.UUID) -> List[TrainingPlan]:
        result = await self.session.execute(
            select(TrainingPlan).where(
                TrainingPlan.trainer_id == trainer_id,
                TrainingPlan.is_template == True,
            )
        )
        return list(result.scalars().all())

    async def get_by_id(self, plan_id: uuid.UUID) -> TrainingPlan | None:
        result = await self.session.execute(
            select(TrainingPlan).where(TrainingPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def create(self, plan: TrainingPlan) -> TrainingPlan:
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update(self, plan: TrainingPlan, data: dict) -> TrainingPlan:
        for key, value in data.items():
            if value is not None:
                setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def list_templates_by_trainer(self, trainer_id: uuid.UUID) -> List[TrainingPlan]:
        return await self.list_by_trainer(trainer_id)

    async def get_client_plan(self, client_id: uuid.UUID) -> TrainingPlan | None:
        result = await self.session.execute(
            select(TrainingPlan).where(
                TrainingPlan.client_id == client_id,
                TrainingPlan.is_template == False,
            ).order_by(
                TrainingPlan.assigned_at.desc(),
                TrainingPlan.updated_at.desc(),
                TrainingPlan.created_at.desc(),
            ).limit(1)
        )
        return result.scalars().first()

    async def count_copies(self, template_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(TrainingPlan).where(
                TrainingPlan.source_template_id == template_id,
                TrainingPlan.is_template == False,
            )
        )
        return int(result.scalar_one() or 0)

    async def detach_template_from_copies(self, template_id: uuid.UUID) -> None:
        await self.session.execute(
            update(TrainingPlan)
            .where(TrainingPlan.source_template_id == template_id)
            .values(source_template_id=None)
        )
        await self.session.commit()

    async def delete(self, plan: TrainingPlan) -> None:
        await self.session.delete(plan)
        await self.session.commit()
