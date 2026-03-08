import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.monthly_report import MonthlyReport
from app.repositories.interface.monthlyReportInterface import MonthlyReportRepositoryInterface


class MonthlyReportRepository(MonthlyReportRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_client(self, client_id: uuid.UUID) -> List[MonthlyReport]:
        result = await self.session.execute(
            select(MonthlyReport)
            .where(MonthlyReport.client_id == client_id)
            .order_by(MonthlyReport.month.desc())
        )
        return list(result.scalars().all())

    async def get_by_client_and_month(self, client_id: uuid.UUID, month: str) -> Optional[MonthlyReport]:
        result = await self.session.execute(
            select(MonthlyReport).where(
                MonthlyReport.client_id == client_id,
                MonthlyReport.month == month,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, report: MonthlyReport) -> MonthlyReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report
