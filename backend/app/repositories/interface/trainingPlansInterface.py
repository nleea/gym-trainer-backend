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

    @abstractmethod
    async def list_templates_by_trainer(self, trainer_id: UUID) -> List[TrainingPlan]:
        pass

    @abstractmethod
    async def get_client_plan(self, client_id: UUID) -> TrainingPlan | None:
        pass

    @abstractmethod
    async def count_copies(self, template_id: UUID) -> int:
        pass

    @abstractmethod
    async def detach_template_from_copies(self, template_id: UUID) -> None:
        pass

    @abstractmethod
    async def delete(self, plan: TrainingPlan) -> None:
        pass
