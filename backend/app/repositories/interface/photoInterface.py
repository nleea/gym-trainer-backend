from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.models.photo import Photo, PhotoType


class PhotoRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, photo: Photo) -> Photo:
        pass

    @abstractmethod
    async def get_by_client_and_type(
        self, client_id: UUID, photo_type: PhotoType, limit: int = 50
    ) -> List[Photo]:
        pass

    @abstractmethod
    async def get_by_id(self, photo_id: UUID) -> Photo | None:
        pass

    @abstractmethod
    async def delete(self, photo: Photo) -> None:
        pass
