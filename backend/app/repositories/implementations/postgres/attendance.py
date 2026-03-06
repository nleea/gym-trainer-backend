import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.attendance import Attendance
from app.repositories.interface.attendanceInterface import AttendanceRepositoryInterface


class AttendanceRepository(AttendanceRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list_by_trainer(self, trainer_id: uuid.UUID) -> List[Attendance]:
        result = await self.session.execute(
            select(Attendance).where(Attendance.trainer_id == trainer_id).order_by(Attendance.date.desc())
        )
        return list(result.scalars().all())

    async def list_by_client(self, client_id: uuid.UUID) -> List[Attendance]:
        result = await self.session.execute(
            select(Attendance).where(Attendance.client_id == client_id).order_by(Attendance.date.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, attendance_id: uuid.UUID) -> Attendance | None:
        result = await self.session.execute(
            select(Attendance).where(Attendance.id == attendance_id)
        )
        return result.scalar_one_or_none()

    async def create(self, record: Attendance) -> Attendance:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(self, record: Attendance, data: dict) -> Attendance:
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        record.updated_at = datetime.utcnow()
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return record

