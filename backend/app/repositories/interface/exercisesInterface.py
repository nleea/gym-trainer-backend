from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.models.exercise import Exercise


class ExercisesRepositoryInterface(ABC):
    @abstractmethod
    async def list_all(self, trainer_id: Optional[UUID] = None) -> List[Exercise]:
        """Devuelve ejercicios globales + los del trainer especificado."""
        pass

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        pass

    @abstractmethod
    async def create(self, exercise: Exercise) -> Exercise:
        pass

    @abstractmethod
    async def update(self, exercise: Exercise, data: dict) -> Exercise:
        pass

    @abstractmethod
    async def delete(self, exercise: Exercise) -> None:
        pass
