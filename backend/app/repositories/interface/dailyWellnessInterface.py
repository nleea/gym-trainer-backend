from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.models.daily_wellness import DailyWellness


class DailyWellnessRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, record: DailyWellness) -> DailyWellness:
        pass

    @abstractmethod
    async def get_by_client_and_date(self, client_id: UUID, log_date: date) -> Optional[DailyWellness]:
        pass

    @abstractmethod
    async def list_by_client_date_range(
        self, client_id: UUID, from_date: date, to_date: date,
    ) -> List[DailyWellness]:
        pass
