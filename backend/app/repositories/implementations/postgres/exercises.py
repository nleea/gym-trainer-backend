import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from app.models.exercise import Exercise
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface


class ExercisesRepository(ExercisesRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, trainer_id: Optional[uuid.UUID] = None) -> List[Exercise]:
        """Ejercicios globales (trainer_id IS NULL) + los propios del trainer."""
        query = select(Exercise).order_by(Exercise.name)
        if trainer_id:
            query = query.where(
                or_(Exercise.trainer_id == None, Exercise.trainer_id == trainer_id)
            )
        else:
            query = query.where(Exercise.trainer_id == None)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, exercise_id: uuid.UUID) -> Exercise | None:
        result = await self.session.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        return result.scalar_one_or_none()

    async def create(self, exercise: Exercise) -> Exercise:
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def update(self, exercise: Exercise, data: dict) -> Exercise:
        for key, value in data.items():
            if value is not None:
                setattr(exercise, key, value)
        exercise.updated_at = datetime.utcnow()
        self.session.add(exercise)
        await self.session.commit()
        await self.session.refresh(exercise)
        return exercise

    async def delete(self, exercise: Exercise) -> None:
        await self.session.delete(exercise)
        await self.session.commit()
