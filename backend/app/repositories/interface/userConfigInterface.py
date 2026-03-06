from abc import ABC, abstractmethod

from app.models.user_config import UserConfig


class UserConfigRepositoryInterface(ABC):

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> UserConfig | None:
        pass

    @abstractmethod
    async def upsert(self, user_id: str, config: dict) -> UserConfig:
        pass
