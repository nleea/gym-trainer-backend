import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import get_current_user, require_trainer
from datetime import date

from app.dependencies import get_achievements_service, get_clients_service, get_metrics_service, get_one_rep_max_service, get_streak_service, get_wellness_insights_service
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientSummaryResponse, ClientUpdate, WorkoutSummaryResponse, WeeklyVolumeItem, HeatmapItem
from app.schemas.achievement import AchievementItem, AchievementSummaryResponse
from app.schemas.metric import MetricsSummaryResponse
from app.schemas.one_rep_max import ExerciseProgressItem, LoggedExerciseItem, OneRepMaxItem
from app.schemas.rpe import RPEHistoryItem
from app.schemas.streak import StreakResponse
from app.schemas.wellness_insights import WellnessCorrelationResponse, WellnessSummaryResponse
from app.services.wellness_insights import WellnessInsightsService
from app.services.achievements import AchievementsService
from app.services.streak import StreakService
from app.services.metrics import MetricsService
from app.services.clients import ClientsService
from app.services.one_rep_max import OneRepMaxService

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
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    timezone_name = request.headers.get("X-Timezone")
    if current_user.role == "trainer":
        return await service.get_client_summary(client_id, trainer=current_user, timezone_name=timezone_name)
    else:
        return await service.get_client_summary(
            client_id,
            trainer=None,
            requesting_client=current_user,
            timezone_name=timezone_name,
        )


@router.get("/{client_id}/workout-summary", response_model=WorkoutSummaryResponse)
async def get_workout_summary(
    client_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ClientsService = Depends(get_clients_service),
):
    timezone_name = request.headers.get("X-Timezone")
    return await service.get_workout_summary(client_id, current_user, timezone_name=timezone_name)


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


@router.get("/{client_id}/logged-exercises", response_model=List[LoggedExerciseItem])
async def get_logged_exercises(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: OneRepMaxService = Depends(get_one_rep_max_service),
):
    return await service.get_logged_exercises(client_id, current_user)


@router.get("/{client_id}/one-rep-max", response_model=List[OneRepMaxItem])
async def get_one_rep_max(
    client_id: uuid.UUID,
    exercise_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: OneRepMaxService = Depends(get_one_rep_max_service),
):
    return await service.get_one_rep_max_history(client_id, exercise_id, current_user)


@router.get("/{client_id}/exercise-progress", response_model=List[ExerciseProgressItem])
async def get_exercise_progress(
    client_id: uuid.UUID,
    exercise_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: OneRepMaxService = Depends(get_one_rep_max_service),
):
    return await service.get_exercise_progress(client_id, exercise_id, current_user)


@router.get("/{client_id}/streak", response_model=StreakResponse)
async def get_streak(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: StreakService = Depends(get_streak_service),
):
    return await service.get_streak(client_id, current_user)


@router.get("/{client_id}/rpe-history", response_model=List[RPEHistoryItem])
async def get_rpe_history(
    client_id: uuid.UUID,
    exercise_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    service: OneRepMaxService = Depends(get_one_rep_max_service),
):
    return await service.get_rpe_history(client_id, exercise_id, current_user)


@router.get("/{client_id}/achievements", response_model=List[AchievementItem])
async def list_achievements(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AchievementsService = Depends(get_achievements_service),
):
    return await service.list_achievements(client_id, current_user)


@router.get("/{client_id}/achievements/summary", response_model=AchievementSummaryResponse)
async def get_achievements_summary(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AchievementsService = Depends(get_achievements_service),
):
    return await service.get_summary(client_id, current_user)


@router.post("/{client_id}/achievements/{achievement_id}/check", status_code=204)
async def check_achievement(
    client_id: uuid.UUID,
    achievement_id: uuid.UUID,
    progress: int = Query(...),
    service: AchievementsService = Depends(get_achievements_service),
):
    await service.check_achievement(client_id, achievement_id, progress)


@router.get("/{client_id}/wellness-summary", response_model=WellnessSummaryResponse)
async def get_wellness_summary(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: WellnessInsightsService = Depends(get_wellness_insights_service),
):
    return await service.get_wellness_summary(client_id, current_user)


@router.get("/{client_id}/wellness-correlation", response_model=WellnessCorrelationResponse)
async def get_wellness_correlation(
    client_id: uuid.UUID,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    service: WellnessInsightsService = Depends(get_wellness_insights_service),
):
    return await service.get_wellness_correlation(client_id, from_date, to_date, current_user)
