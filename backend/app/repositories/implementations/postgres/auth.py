import uuid


from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.models.client import Client
from app.repositories.interface.authInterface import AuthRepositoryInterface


class AuthRepository(AuthRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Tuple[User, Client] | Tuple[None, None]:
        result = await self.session.execute(
            select(User, Client)
            .outerjoin(Client, User.id == Client.user_id)
            .where(User.email == email)
        )
        row = result.first()
        if row is None:
            return None
        return row.User, row.Client

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
