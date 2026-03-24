import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_metrics_service, get_volume_metrics_service
from app.models.user import User
from app.schemas.metric import (
    MetricCreate,
    MetricPhotoUploadRequest,
    MetricPhotoUploadResponse,
    MetricResponse,
    MetricUpdate,
)
from app.schemas.volume_metrics import AdherenceResponse, VolumeResponse
from app.services.metrics import MetricsService
from app.services.volume_metrics import VolumeMetricsService

router = APIRouter()


@router.post("", response_model=MetricResponse, status_code=201)
async def create_metric(
    data: MetricCreate,
    current_user: User = Depends(require_client),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.create_metric(data, current_user)


@router.post("/upload-url", response_model=MetricPhotoUploadResponse)
async def create_metric_upload_url(
    data: MetricPhotoUploadRequest,
    current_user: User = Depends(require_client),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.create_photo_upload_url(data, current_user)


@router.get("/volume", response_model=VolumeResponse)
async def get_weekly_volume(
    client_id: uuid.UUID = Query(...),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    service: VolumeMetricsService = Depends(get_volume_metrics_service),
):
    return await service.get_weekly_volume(client_id, from_date, to_date, current_user)


@router.get("/adherence", response_model=AdherenceResponse)
async def get_adherence_rate(
    client_id: uuid.UUID = Query(...),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    service: VolumeMetricsService = Depends(get_volume_metrics_service),
):
    return await service.get_adherence_rate(client_id, from_date, to_date, current_user)


@router.get("/{client_id}", response_model=List[MetricResponse])
async def list_metrics(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.list_metrics(client_id, current_user)


@router.put("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: uuid.UUID,
    data: MetricUpdate,
    current_user: User = Depends(require_client),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.update_metric(metric_id, data, current_user)


@router.delete("/{metric_id}", status_code=204)
async def delete_metric(
    metric_id: uuid.UUID,
    current_user: User = Depends(require_client),
    service: MetricsService = Depends(get_metrics_service),
):
    await service.delete_metric(metric_id, current_user)
