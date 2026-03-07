import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_current_user, require_trainer
from app.dependencies import get_exercises_service
from app.models.user import User
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSyncResponse,
    ExerciseUpdate,
    FavoriteExerciseResponse,
)
from app.services.exercises import ExercisesService

router = APIRouter()


@router.get("", response_model=ExerciseListResponse)
async def list_exercises(
    body_part: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    favorites_only: bool = Query(False),
    user_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.list_exercises(
        current_user=current_user,
        body_part=body_part,
        equipment=equipment,
        q=q,
        favorites_only=favorites_only,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=list[ExerciseResponse])
async def search_exercises(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.search_exercises(q=q, current_user=current_user, limit=limit)


@router.get("/body-parts", response_model=list[str])
async def list_body_parts(
    _: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.list_body_parts()


@router.get("/equipment", response_model=list[str])
async def list_equipment(
    _: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.list_equipment()


@router.post("/sync", response_model=ExerciseSyncResponse)
async def sync_exercises(
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.sync_exercises(current_user)


@router.post("/{exercise_id}/favorite", response_model=FavoriteExerciseResponse)
async def add_favorite(
    exercise_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.add_favorite(current_user, exercise_id)


@router.delete("/{exercise_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    exercise_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    await service.remove_favorite(current_user, exercise_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/favorites", response_model=list[ExerciseResponse])
async def list_favorites(
    user_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.list_favorites(current_user, user_id=user_id)


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    data: ExerciseCreate,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    exercise = await service.create_custom(data, current_user)
    return ExerciseResponse.model_validate(
        {
            **exercise.model_dump(),
            "secondary_muscles": exercise.secondary_muscles or [],
            "instructions": exercise.instructions or [],
            "is_favorite": False,
        }
    )


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: uuid.UUID,
    data: ExerciseUpdate,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    exercise = await service.update_custom(exercise_id, data, current_user)
    return ExerciseResponse.model_validate(
        {
            **exercise.model_dump(),
            "secondary_muscles": exercise.secondary_muscles or [],
            "instructions": exercise.instructions or [],
            "is_favorite": False,
        }
    )


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    await service.delete_custom(exercise_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
