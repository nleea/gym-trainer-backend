import uuid
from pathlib import Path
from typing import List

import boto3
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.metric import Metric
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.metricsInterface import MetricsRepositoryInterface
from app.schemas.metric import (
    MetricCreate,
    MetricPhotoUploadRequest,
    MetricPhotoUploadResponse,
    MetricResponse,
    MetricsSummaryResponse,
    MetricUpdate,
)


class MetricsService:
    def __init__(
        self,
        metrics_repo: MetricsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.metrics_repo = metrics_repo
        self.clients_repo = clients_repo

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        base = Path(file_name).name.strip()
        return base if base else "photo.jpg"

    @staticmethod
    def _assert_upload_is_valid(upload: MetricPhotoUploadRequest) -> None:
        if not upload.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image uploads are allowed",
            )
        if upload.file_size is not None and upload.file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image exceeds 10MB limit",
            )

    @staticmethod
    def _r2_endpoint() -> str:
        if settings.R2_ENDPOINT_URL:
            return settings.R2_ENDPOINT_URL.rstrip("/")
        if settings.R2_ACCOUNT_ID:
            return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        return ""

    @staticmethod
    def _assert_r2_configured() -> None:
        required = [
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
            settings.R2_BUCKET_NAME,
        ]
        if not all(required) or not MetricsService._r2_endpoint():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="R2 upload is not configured on server",
            )

    async def _assert_can_access_client(self, client_id: uuid.UUID, current_user: User) -> None:
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

    async def list_metrics(self, client_id: uuid.UUID, current_user: User) -> List[Metric]:
        await self._assert_can_access_client(client_id, current_user)
        return await self.metrics_repo.list_by_client(client_id)

    async def create_metric(self, data: MetricCreate, current_user: User) -> Metric:
        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
            )
        metric = Metric(
            client_id=client.id,
            **data.model_dump(exclude_none=False),
        )
        return await self.metrics_repo.create(metric)

    async def update_metric(
        self, metric_id: uuid.UUID, data: MetricUpdate, current_user: User
    ) -> Metric:
        metric = await self.metrics_repo.get_by_id(metric_id)
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client or metric.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.metrics_repo.update(metric, data.model_dump(exclude_none=True))

    async def delete_metric(self, metric_id: uuid.UUID, current_user: User) -> None:
        metric = await self.metrics_repo.get_by_id(metric_id)
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client or metric.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await self.metrics_repo.delete(metric)

    async def get_metrics_summary(
        self, client_id: uuid.UUID, current_user: User
    ) -> MetricsSummaryResponse:
        await self._assert_can_access_client(client_id, current_user)
        raw = await self.metrics_repo.get_summary(client_id)

        deltas = {}
        for key, (last_val, prev_val) in raw["deltas"].items():
            change = round(last_val - prev_val, 2) if last_val is not None and prev_val is not None else None
            deltas[key] = {"lastValue": last_val, "change": change}

        history = [MetricResponse.model_validate(m) for m in raw["history"]]

        return MetricsSummaryResponse(
            deltas=deltas,
            series=raw["series"],
            history=history,
        )

    async def create_photo_upload_url(
        self, upload: MetricPhotoUploadRequest, current_user: User
    ) -> MetricPhotoUploadResponse:
        self._assert_upload_is_valid(upload)
        self._assert_r2_configured()

        print('APSO')
        
        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        safe_name = self._sanitize_filename(upload.file_name)
        ext = Path(safe_name).suffix or ".jpg"
        key = f"clients/{client.id}/metrics/{uuid.uuid4().hex}{ext}"

        endpoint = self._r2_endpoint()
        bucket = str(settings.R2_BUCKET_NAME)
        expires = int(settings.R2_UPLOAD_URL_EXPIRES)

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": upload.content_type,
            },
            ExpiresIn=expires,
        )

        public_base = (
            settings.R2_PUBLIC_BASE_URL.rstrip("/")
            if settings.R2_PUBLIC_BASE_URL
            else f"{endpoint}/{bucket}"
        )

        return MetricPhotoUploadResponse(
            key=key,
            upload_url=upload_url,
            public_url=f"{public_base}/{key}",
            expires_in=expires,
        )
