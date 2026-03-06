from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from app.models.progress_entry import ProgressEntry


class ProgressRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_client(self, client_id: UUID) -> List[ProgressEntry]:
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> ProgressEntry | None:
        pass

    @abstractmethod
    async def create(self, entry: ProgressEntry) -> ProgressEntry:
        pass
