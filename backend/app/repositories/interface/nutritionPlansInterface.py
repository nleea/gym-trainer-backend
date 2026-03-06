from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from app.models.nutrition_plan import NutritionPlan


class NutritionPlansRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_trainer(self, trainer_id: UUID) -> List[NutritionPlan]:
        pass

    @abstractmethod
    async def get_by_id(self, plan_id: UUID) -> NutritionPlan | None:
        pass

    @abstractmethod
    async def create(self, plan: NutritionPlan) -> NutritionPlan:
        pass

    @abstractmethod
    async def update(self, plan: NutritionPlan, data: dict) -> NutritionPlan:
        pass
