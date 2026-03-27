import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.daily_wellness import DailyWellness
from app.repositories.interface.dailyWellnessInterface import DailyWellnessRepositoryInterface


class DailyWellnessRepository(DailyWellnessRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: DailyWellness) -> DailyWellness:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_client_and_date(self, client_id: uuid.UUID, log_date: date) -> Optional[DailyWellness]:
        result = await self.session.execute(
            select(DailyWellness).where(
                DailyWellness.client_id == client_id,
                DailyWellness.date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_client_date_range(
        self, client_id: uuid.UUID, from_date: date, to_date: date,
    ) -> List[DailyWellness]:
        result = await self.session.execute(
            select(DailyWellness)
            .where(
                DailyWellness.client_id == client_id,
                DailyWellness.date >= from_date,
                DailyWellness.date <= to_date,
            )
            .order_by(DailyWellness.date.asc())
        )
        return list(result.scalars().all())
