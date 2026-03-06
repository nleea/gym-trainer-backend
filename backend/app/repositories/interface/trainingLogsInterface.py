from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import Any, Dict, List, Optional

from app.models.training_log import TrainingLog


class TrainingLogsRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_filters(
        self,
        client_id: Optional[UUID] = None,
        week_start: Optional[date] = None,
    ) -> List[TrainingLog]:
        pass

    @abstractmethod
    async def get_by_id(self, log_id: UUID) -> TrainingLog | None:
        pass

    @abstractmethod
    async def get_by_client_and_date(self, client_id: UUID, log_date: date) -> TrainingLog | None:
        pass

    @abstractmethod
    async def list_by_client_week(self, client_id: UUID, week_start: date) -> List[TrainingLog]:
        pass

    @abstractmethod
    async def create(self, log: TrainingLog) -> TrainingLog:
        pass

    @abstractmethod
    async def update(self, log: TrainingLog, data: dict) -> TrainingLog:
        pass

    @abstractmethod
    async def get_weekly_volume(self, client_id: UUID, weeks: int = 12) -> List[Dict[str, Any]]:
        """Returns [{week: 'YYYY-MM-DD', volume: float}] for the last N weeks."""
        pass

    @abstractmethod
    async def get_workout_heatmap(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Returns [{date: 'YYYY-MM-DD', count: int, volume: float}] for the last 12 months (only days with workouts)."""
        pass

    @abstractmethod
    async def get_last_performance(self, client_id: UUID, exercise_ids: List[str]) -> List[Dict[str, Any]]:
        """Returns [{exercise_id, date, reps, weight}] — last logged weight per exercise."""
        pass

    @abstractmethod
    async def get_max_weights_before_date(self, client_id: UUID, log_date: date) -> Dict[str, float]:
        """Returns {exercise_id: max_weight} for all exercises logged before log_date."""
        pass
