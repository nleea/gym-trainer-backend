from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user_config import UserConfig
from app.repositories.interface.userConfigInterface import UserConfigRepositoryInterface


class UserConfigRepository(UserConfigRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: str) -> UserConfig | None:
        result = await self.session.execute(
            select(UserConfig).where(UserConfig.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: str, config: dict) -> UserConfig:
        existing = await self.get_by_user_id(user_id)
        if existing:
            existing.config = config
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            record = UserConfig(user_id=user_id, config=config)
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)
            return record
