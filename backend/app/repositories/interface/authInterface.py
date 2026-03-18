from abc import ABC, abstractmethod
from uuid import UUID
from typing import Tuple
from app.models.user import User
from app.models.client import Client
from app.models.user_session import UserSession

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

    @abstractmethod
    async def create_user_session(self, session: UserSession) -> UserSession:
        pass

    @abstractmethod
    async def get_session_by_id(self, session_id: UUID, *, for_update: bool = False) -> UserSession | None:
        pass

    @abstractmethod
    async def get_session_by_jti(self, refresh_jti: str) -> UserSession | None:
        pass

    @abstractmethod
    async def update_user_session(self, session: UserSession) -> UserSession:
        pass

    @abstractmethod
    async def list_active_sessions(self, user_id: UUID) -> list[UserSession]:
        pass
