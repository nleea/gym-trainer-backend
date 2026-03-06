from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from app.models.client import Client


class ClientsRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_trainer(self, trainer_id: UUID) -> List[Client]:
        pass

    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> Client | None:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Client | None:
        pass

    @abstractmethod
    async def create(self, client: Client) -> Client:
        pass

    @abstractmethod
    async def update(self, client: Client, data: dict) -> Client:
        pass
