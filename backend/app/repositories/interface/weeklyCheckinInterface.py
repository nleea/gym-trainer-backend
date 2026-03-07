from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import List

from app.models.weekly_checkin import WeeklyCheckin


class WeeklyCheckinRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_id(self, checkin_id: UUID) -> WeeklyCheckin | None:
        pass

    @abstractmethod
    async def get_by_client_and_week(self, client_id: UUID, week_start: date) -> WeeklyCheckin | None:
        pass

    @abstractmethod
    async def list_by_client(self, client_id: UUID) -> List[WeeklyCheckin]:
        pass

    @abstractmethod
    async def create(self, checkin: WeeklyCheckin) -> WeeklyCheckin:
        pass

    @abstractmethod
    async def update(self, checkin: WeeklyCheckin, data: dict) -> WeeklyCheckin:
        pass
