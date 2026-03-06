import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.meal_log import MealLog
from app.repositories.interface.mealLogsInterface import MealLogsRepositoryInterface


class MealLogsRepository(MealLogsRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_filters(
        self,
        client_id: Optional[uuid.UUID] = None,
        log_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[MealLog]:
        query = select(MealLog)
        if client_id:
            query = query.where(MealLog.client_id == client_id)
        if log_date:
            query = query.where(MealLog.date == log_date)
        if start_date:
            query = query.where(MealLog.date >= start_date)
        if end_date:
            query = query.where(MealLog.date <= end_date)
        result = await self.session.execute(query.order_by(MealLog.date.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, log_id: uuid.UUID) -> MealLog | None:
        result = await self.session.execute(
            select(MealLog).where(MealLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_date_meal_key(
        self, client_id: uuid.UUID, log_date: date, meal_key: str
    ) -> MealLog | None:
        result = await self.session.execute(
            select(MealLog)
            .where(MealLog.client_id == client_id)
            .where(MealLog.date == log_date)
            .where(MealLog.meal_key == meal_key)
        )
        return result.scalar_one_or_none()

    async def create(self, log: MealLog) -> MealLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def update(self, log: MealLog, data: dict) -> MealLog:
        for key, value in data.items():
            setattr(log, key, value)
        log.updated_at = datetime.utcnow()
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def delete(self, log: MealLog) -> None:
        await self.session.delete(log)
        await self.session.commit()
