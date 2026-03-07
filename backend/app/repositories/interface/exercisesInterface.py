from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.models.exercise import Exercise
from app.models.exercise_favorite import ExerciseFavorite


class ExercisesRepositoryInterface(ABC):
    @abstractmethod
    async def list_exercises(
        self,
        *,
        body_part: Optional[str] = None,
        equipment: Optional[str] = None,
        q: Optional[str] = None,
        favorites_only: bool = False,
        user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Exercise], int]:
        pass

    @abstractmethod
    async def search_by_name(self, q: str, limit: int = 20) -> list[Exercise]:
        pass

    @abstractmethod
    async def list_body_parts(self) -> list[str]:
        pass

    @abstractmethod
    async def list_equipment(self) -> list[str]:
        pass

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        pass

    @abstractmethod
    async def upsert_many_from_external(self, items: list[dict[str, Any]], synced_at: datetime) -> tuple[int, int]:
        """Returns (created_count, updated_count)."""
        pass

    @abstractmethod
    async def add_favorite(self, user_id: UUID, exercise_id: UUID) -> ExerciseFavorite:
        pass

    @abstractmethod
    async def remove_favorite(self, user_id: UUID, exercise_id: UUID) -> bool:
        pass

    @abstractmethod
    async def list_favorites(self, user_id: UUID) -> list[Exercise]:
        pass

    @abstractmethod
    async def favorite_ids_for_user(self, user_id: UUID, exercise_ids: list[UUID]) -> set[UUID]:
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
