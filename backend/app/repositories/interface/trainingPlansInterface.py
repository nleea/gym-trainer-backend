from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from app.models.training_plan import TrainingPlan


class TrainingPlansRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_trainer(self, trainer_id: UUID) -> List[TrainingPlan]:
        pass

    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> TrainingPlan | None:
        pass

    @abstractmethod
    async def create(self, plan: TrainingPlan) -> TrainingPlan:
        pass

    @abstractmethod
    async def update(self, plan: TrainingPlan, data: dict) -> TrainingPlan:
        pass
