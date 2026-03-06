import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.exercise import Exercise
from app.models.user import User
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate


class ExercisesService:
    def __init__(self, exercises_repo: ExercisesRepositoryInterface) -> None:
        self.exercises_repo = exercises_repo

    async def list_exercises(self, current_user: User) -> List[Exercise]:
        trainer_id = current_user.id if current_user.role == "trainer" else None
        return await self.exercises_repo.list_all(trainer_id=trainer_id)

    async def create_exercise(self, data: ExerciseCreate, current_user: User) -> Exercise:
        exercise = Exercise(
            name=data.name,
            muscle_group=data.muscle_group,
            description=data.description,
            trainer_id=current_user.id if current_user.role == "trainer" else None,
        )
        return await self.exercises_repo.create(exercise)

    async def update_exercise(
        self, exercise_id: uuid.UUID, data: ExerciseUpdate, current_user: User
    ) -> Exercise:
        exercise = await self.exercises_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        # Solo el trainer que lo creó puede editarlo (o ejercicios globales por admins)
        if exercise.trainer_id and exercise.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await self.exercises_repo.update(exercise, data.model_dump(exclude_none=True))

    async def delete_exercise(self, exercise_id: uuid.UUID, current_user: User) -> None:
        exercise = await self.exercises_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        if exercise.trainer_id and exercise.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await self.exercises_repo.delete(exercise)
