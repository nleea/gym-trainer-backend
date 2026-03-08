import uuid
from datetime import date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.photo import Photo, PhotoType
from app.repositories.interface.photoInterface import PhotoRepositoryInterface


class PhotoRepository(PhotoRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, photo: Photo) -> Photo:
        self.session.add(photo)
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

    async def get_by_client_and_type(
        self, client_id: uuid.UUID, photo_type: PhotoType, limit: int = 50
    ) -> List[Photo]:
        result = await self.session.execute(
            select(Photo)
            .where(Photo.client_id == client_id, Photo.type == photo_type)
            .order_by(Photo.taken_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, photo_id: uuid.UUID) -> Photo | None:
        result = await self.session.execute(
            select(Photo).where(Photo.id == photo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filters(
        self,
        client_id: uuid.UUID,
        photo_type: PhotoType | None = None,
        week_start: date | None = None,
        week_end: date | None = None,
    ) -> List[Photo]:
        query = select(Photo).where(Photo.client_id == client_id)

        if photo_type:
            query = query.where(Photo.type == photo_type)
        if week_start:
            query = query.where(Photo.taken_at >= week_start)
        if week_end:
            query = query.where(Photo.taken_at <= week_end)

        query = query.order_by(Photo.taken_at.desc(), Photo.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, photo: Photo, data: dict) -> Photo:
        for k, v in data.items():
            setattr(photo, k, v)
        self.session.add(photo)
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

    async def delete(self, photo: Photo) -> None:
        await self.session.delete(photo)
        await self.session.commit()
