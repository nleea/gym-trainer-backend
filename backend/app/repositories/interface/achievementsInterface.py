from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from app.models.achievement import Achievement, ClientAchievement


class AchievementsRepositoryInterface(ABC):
    @abstractmethod
    async def list_all(self) -> List[Achievement]:
        """Return all achievement definitions."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Achievement]:
        pass

    @abstractmethod
    async def get_client_achievements(self, client_id: UUID) -> Dict[UUID, ClientAchievement]:
        """Return {achievement_id: ClientAchievement} for a client."""
        pass

    @abstractmethod
    async def get_or_create_client_achievement(
        self, client_id: UUID, achievement_id: UUID,
    ) -> ClientAchievement:
        """Get existing or create a new ClientAchievement with progress=0."""
        pass

    @abstractmethod
    async def update_client_achievement(
        self, record: ClientAchievement, data: dict,
    ) -> ClientAchievement:
        pass
