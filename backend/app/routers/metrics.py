import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_client
from app.dependencies import get_metrics_service
from app.models.user import User
from app.schemas.metric import MetricCreate, MetricResponse, MetricUpdate
from app.services.metrics import MetricsService

router = APIRouter()


@router.get("/{client_id}", response_model=List[MetricResponse])
async def list_metrics(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.list_metrics(client_id, current_user)


@router.post("", response_model=MetricResponse, status_code=201)
async def create_metric(
    data: MetricCreate,
    current_user: User = Depends(require_client),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.create_metric(data, current_user)


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
