import asyncio
import uuid
from collections import defaultdict
from datetime import date
from typing import Optional

import boto3
from botocore.config import Config
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.photo import Photo, PhotoType
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.photoInterface import PhotoRepositoryInterface
from app.schemas.photo import (
    PhotoResponse,
    PhotoTimelineGroup,
    PhotoTimelineResponse,
    PhotoUploadUrlResponse,
)
from app.schemas.evidence import EvidenceDayResponse, EvidenceItemResponse, EvidenceWeekResponse


class PhotoService:
    def __init__(
        self,
        repo: PhotoRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ):
        self.repo = repo
        self.clients_repo = clients_repo

    def _s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

    async def _assert_access(self, client_id: uuid.UUID, current_user: User) -> None:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if current_user.role == "trainer":
            if client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self.clients_repo.get_by_user_id(current_user.id)
            if not own_client or own_client.id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    def _signed_url(self, r2_key: str, expires: int = 3600) -> str:
        s3 = self._s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": r2_key},
            ExpiresIn=expires,
        )

    def _to_response(self, photo: Photo) -> PhotoResponse:
        return PhotoResponse(
            id=photo.id,
            client_id=photo.client_id,
            uploaded_by=photo.uploaded_by,
            type=photo.type,
            url=self._signed_url(photo.r2_key),
            notes=photo.notes,
            taken_at=photo.taken_at,
            created_at=photo.created_at,
        )

    _ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    _MAX_BYTES = 10 * 1024 * 1024

    async def create_upload_url(
        self,
        client_id: uuid.UUID,
        current_user: User,
        file_name: str,
        content_type: str,
        file_size: Optional[int],
    ) -> PhotoUploadUrlResponse:
        await self._assert_access(client_id, current_user)

        if content_type not in self._ALLOWED_TYPES:
            raise HTTPException(status_code=422, detail="Only jpg, png, webp allowed")
        if file_size and file_size > self._MAX_BYTES:
            raise HTTPException(status_code=422, detail="File too large (max 10 MB)")

        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "jpg"
        r2_key = f"photos/{client_id}/{uuid.uuid4().hex}.{ext}"
        expires = int(settings.R2_UPLOAD_URL_EXPIRES)

        def _presign():
            return self._s3_client().generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.R2_BUCKET_NAME,
                    "Key": r2_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires,
            )

        upload_url = await asyncio.to_thread(_presign)
        return PhotoUploadUrlResponse(r2_key=r2_key, upload_url=upload_url, expires_in=expires)

    async def save_photo_record(
        self,
        client_id: uuid.UUID,
        current_user: User,
        r2_key: str,
        photo_type: PhotoType,
        notes: Optional[str],
        taken_at: date,
    ) -> PhotoResponse:
        await self._assert_access(client_id, current_user)

        photo = Photo(
            client_id=client_id,
            uploaded_by=current_user.id,
            type=photo_type,
            r2_key=r2_key,
            notes=notes,
            taken_at=taken_at,
        )
        saved = await self.repo.create(photo)
        return self._to_response(saved)

    async def get_timeline(
        self, client_id: uuid.UUID, photo_type: PhotoType, current_user: User
    ) -> PhotoTimelineResponse:
        await self._assert_access(client_id, current_user)
        photos = await self.repo.get_by_client_and_type(client_id, photo_type)
        groups_map: dict[date, list[PhotoResponse]] = defaultdict(list)
        for p in photos:
            groups_map[p.taken_at].append(self._to_response(p))
        groups = [
            PhotoTimelineGroup(date=d, photos=ps)
            for d, ps in sorted(groups_map.items(), reverse=True)
        ]
        return PhotoTimelineResponse(type=photo_type, groups=groups)

    async def delete_photo(self, photo_id: uuid.UUID, current_user: User) -> None:
        photo = await self.repo.get_by_id(photo_id)
        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

        if current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(photo.client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self.clients_repo.get_by_user_id(current_user.id)
            if not own_client or own_client.id != photo.client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        r2_key = photo.r2_key

        def _delete():
            self._s3_client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=r2_key)

        await asyncio.to_thread(_delete)
        await self.repo.delete(photo)

    async def list_evidences(
        self,
        client_id: uuid.UUID,
        current_user: User,
        evidence_type: PhotoType | None = None,
        week_start: date | None = None,
        week_end: date | None = None,
    ) -> EvidenceWeekResponse:
        await self._assert_access(client_id, current_user)
        photos = await self.repo.get_by_filters(
            client_id=client_id,
            photo_type=evidence_type,
            week_start=week_start,
            week_end=week_end,
        )

        groups_map: dict[date, list[EvidenceItemResponse]] = defaultdict(list)
        for photo in photos:
            groups_map[photo.taken_at].append(
                EvidenceItemResponse(
                    id=photo.id,
                    client_id=photo.client_id,
                    trainer_id=photo.uploaded_by,
                    type=photo.type.value,
                    date=photo.taken_at,
                    exercise_name="Food evidence",
                    client_note=photo.notes,
                    photo_urls=[self._signed_url(photo.r2_key)],
                    submitted_at=photo.created_at,
                    responded_at=None,
                    created_at=photo.created_at,
                )
            )

        days = [
            EvidenceDayResponse(date=d, label=d.strftime("%A"), evidences=items)
            for d, items in sorted(groups_map.items(), reverse=True)
        ]
        return EvidenceWeekResponse(week_start=week_start, week_end=week_end, days=days)
