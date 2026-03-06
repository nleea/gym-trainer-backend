import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.client import Client
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface


class ClientsRepository(ClientsRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_trainer(self, trainer_id: uuid.UUID) -> List[Client]:
        result = await self.session.execute(
            select(Client).where(Client.trainer_id == trainer_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, client: Client) -> Client:
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def update(self, client: Client, data: dict) -> Client:
        for key, value in data.items():
            if value is not None:
                setattr(client, key, value)
        client.updated_at = datetime.utcnow()
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client
