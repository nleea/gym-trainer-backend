from abc import ABC, abstractmethod
from uuid import UUID
from typing import Tuple
from app.models.user import User
from app.models.client import Client

class AuthRepositoryInterface(ABC):
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Tuple[User, Client] | Tuple[None, None]:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def create_user(self, user: User) -> User:
        pass
