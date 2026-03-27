import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.achievement import Achievement, ClientAchievement
from app.repositories.interface.achievementsInterface import AchievementsRepositoryInterface


class AchievementsRepository(AchievementsRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[Achievement]:
        result = await self.session.execute(
            select(Achievement).order_by(Achievement.category, Achievement.target)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[Achievement]:
        result = await self.session.execute(
            select(Achievement).where(Achievement.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_client_achievements(self, client_id: uuid.UUID) -> Dict[uuid.UUID, ClientAchievement]:
        result = await self.session.execute(
            select(ClientAchievement).where(ClientAchievement.client_id == client_id)
        )
        return {ca.achievement_id: ca for ca in result.scalars().all()}

    async def get_or_create_client_achievement(
        self, client_id: uuid.UUID, achievement_id: uuid.UUID,
    ) -> ClientAchievement:
        result = await self.session.execute(
            select(ClientAchievement).where(
                ClientAchievement.client_id == client_id,
                ClientAchievement.achievement_id == achievement_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return record

        record = ClientAchievement(
            client_id=client_id,
            achievement_id=achievement_id,
            progress=0,
            unlocked=False,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update_client_achievement(
        self, record: ClientAchievement, data: dict,
    ) -> ClientAchievement:
        for key, value in data.items():
            setattr(record, key, value)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
