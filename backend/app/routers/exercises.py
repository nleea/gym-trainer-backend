import uuid
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_trainer
from app.dependencies import get_exercises_service
from app.models.user import User
from app.schemas.exercise import ExerciseCreate, ExerciseResponse, ExerciseUpdate
from app.services.exercises import ExercisesService

router = APIRouter()


@router.get("", response_model=List[ExerciseResponse])
async def list_exercises(
    current_user: User = Depends(get_current_user),
    service: ExercisesService = Depends(get_exercises_service),
):
    """Devuelve ejercicios globales + los creados por el trainer autenticado."""
    return await service.list_exercises(current_user)


@router.post("", response_model=ExerciseResponse, status_code=201)
async def create_exercise(
    data: ExerciseCreate,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.create_exercise(data, current_user)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: uuid.UUID,
    data: ExerciseUpdate,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    return await service.update_exercise(exercise_id, data, current_user)


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: uuid.UUID,
    current_user: User = Depends(require_trainer),
    service: ExercisesService = Depends(get_exercises_service),
):
    await service.delete_exercise(exercise_id, current_user)
