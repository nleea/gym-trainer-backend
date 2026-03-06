import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_trainer
from app.dependencies import get_clients_service
from app.models.user import User
from app.dependencies import get_metrics_service
from app.schemas.client import ClientCreate, ClientResponse, ClientSummaryResponse, ClientUpdate, WorkoutSummaryResponse, WeeklyVolumeItem, HeatmapItem
from app.schemas.metric import MetricsSummaryResponse
from app.services.metrics import MetricsService
from app.services.clients import ClientsService

router = APIRouter()


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    trainer: User = Depends(require_trainer),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.list_clients(trainer)


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    trainer: User = Depends(require_trainer),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.create_client(data, trainer)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    
    if current_user.role == "trainer":
        return await service.get_client(client_id, trainer=current_user)
    else:
        return await service.get_client(client_id, trainer=None, requesting_client=current_user)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    trainer: User = Depends(require_trainer),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.update_client(client_id, data, trainer)


@router.get("/{client_id}/summary", response_model=ClientSummaryResponse)
async def get_client_summary(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    if current_user.role == "trainer":
        return await service.get_client_summary(client_id, trainer=current_user)
    else:
        return await service.get_client_summary(client_id, trainer=None, requesting_client=current_user)


@router.get("/{client_id}/workout-summary", response_model=WorkoutSummaryResponse)
async def get_workout_summary(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.get_workout_summary(client_id, current_user)


@router.get("/{client_id}/metrics-summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: MetricsService = Depends(get_metrics_service),
):
    return await service.get_metrics_summary(client_id, current_user)


@router.get("/{client_id}/weekly-volume", response_model=list[WeeklyVolumeItem])
async def get_weekly_volume(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.get_weekly_volume(client_id, current_user)


@router.get("/{client_id}/workout-heatmap", response_model=list[HeatmapItem])
async def get_workout_heatmap(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    return await service.get_workout_heatmap(client_id, current_user)
