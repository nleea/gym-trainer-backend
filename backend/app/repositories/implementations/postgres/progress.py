import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.progress_entry import ProgressEntry
from app.repositories.interface.progressInterface import ProgressRepositoryInterface


class ProgressRepository(ProgressRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_client(self, client_id: uuid.UUID) -> List[ProgressEntry]:
        result = await self.session.execute(
            select(ProgressEntry)
            .where(ProgressEntry.client_id == client_id)
            .order_by(ProgressEntry.date.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, entry_id: uuid.UUID) -> ProgressEntry | None:
        result = await self.session.execute(
            select(ProgressEntry).where(ProgressEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def create(self, entry: ProgressEntry) -> ProgressEntry:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry
