from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import List, Optional

from app.models.meal_log import MealLog


class MealLogsRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_filters(
        self,
        client_id: Optional[UUID] = None,
        log_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[MealLog]:
        pass

    @abstractmethod
    async def get_by_id(self, log_id: UUID) -> MealLog | None:
        pass

    @abstractmethod
    async def get_by_client_date_meal_key(
        self, client_id: UUID, log_date: date, meal_key: str
    ) -> MealLog | None:
        pass

    @abstractmethod
    async def create(self, log: MealLog) -> MealLog:
        pass

    @abstractmethod
    async def update(self, log: MealLog, data: dict) -> MealLog:
        pass

    @abstractmethod
    async def delete(self, log: MealLog) -> None:
        pass
