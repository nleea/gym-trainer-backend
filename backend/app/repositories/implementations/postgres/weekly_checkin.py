import uuid
from datetime import date, datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.weekly_checkin import WeeklyCheckin
from app.repositories.interface.weeklyCheckinInterface import WeeklyCheckinRepositoryInterface


class WeeklyCheckinRepository(WeeklyCheckinRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, checkin_id: uuid.UUID) -> WeeklyCheckin | None:
        result = await self.session.execute(
            select(WeeklyCheckin).where(WeeklyCheckin.id == checkin_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_and_week(self, client_id: uuid.UUID, week_start: date) -> WeeklyCheckin | None:
        result = await self.session.execute(
            select(WeeklyCheckin).where(
                WeeklyCheckin.client_id == client_id,
                WeeklyCheckin.week_start == week_start,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_client(self, client_id: uuid.UUID) -> List[WeeklyCheckin]:
        result = await self.session.execute(
            select(WeeklyCheckin)
            .where(WeeklyCheckin.client_id == client_id)
            .order_by(WeeklyCheckin.week_start.desc())
        )
        return list(result.scalars().all())

    async def create(self, checkin: WeeklyCheckin) -> WeeklyCheckin:
        self.session.add(checkin)
        await self.session.commit()
        await self.session.refresh(checkin)
        return checkin

    async def update(self, checkin: WeeklyCheckin, data: dict) -> WeeklyCheckin:
        for key, value in data.items():
            setattr(checkin, key, value)
        checkin.updated_at = datetime.utcnow()
        self.session.add(checkin)
        await self.session.commit()
        await self.session.refresh(checkin)
        return checkin
