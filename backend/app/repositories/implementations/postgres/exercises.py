from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, delete, distinct, select

from app.models.exercise import Exercise
from app.models.exercise_favorite import ExerciseFavorite
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface


class ExercisesRepository(ExercisesRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_exercises(
        self,
        *,
        body_part: Optional[str] = None,
        equipment: Optional[str] = None,
        q: Optional[str] = None,
        favorites_only: bool = False,
        user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Exercise], int]:
        filters = [Exercise.external_id.is_(None)]
        if body_part:
            filters.append(func.lower(Exercise.body_part) == body_part.strip().lower())
        if equipment:
            filters.append(func.lower(Exercise.equipment) == equipment.strip().lower())
        if q:
            filters.append(func.lower(Exercise.name).like(f"%{q.strip().lower()}%"))

        if favorites_only and user_id:
            base = (
                select(Exercise)
                .join(ExerciseFavorite, ExerciseFavorite.exercise_id == Exercise.id)
                .where(and_(*filters), ExerciseFavorite.user_id == user_id)
            )
            count_stmt = (
                select(func.count())
                .select_from(Exercise)
                .join(ExerciseFavorite, ExerciseFavorite.exercise_id == Exercise.id)
                .where(and_(*filters), ExerciseFavorite.user_id == user_id)
            )
        else:
            base = select(Exercise).where(and_(*filters))
            count_stmt = select(func.count()).select_from(Exercise).where(and_(*filters))

        rows = await self.session.execute(
            base.order_by(Exercise.name).limit(limit).offset(offset)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())
        return list(rows.scalars().all()), total

    async def search_by_name(self, q: str, limit: int = 20) -> list[Exercise]:
        stmt = (
            select(Exercise)
            .where(
                Exercise.external_id.is_not(None),
                func.lower(Exercise.name).like(f"%{q.strip().lower()}%"),
            )
            .order_by(Exercise.name)
            .limit(limit)
        )
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def list_body_parts(self) -> list[str]:
        rows = await self.session.execute(
            select(distinct(Exercise.body_part))
            .where(Exercise.body_part.is_not(None), Exercise.external_id.is_not(None))
            .order_by(Exercise.body_part)
        )
        return [str(value) for value in rows.scalars().all() if value]

    async def list_equipment(self) -> list[str]:
        rows = await self.session.execute(
            select(distinct(Exercise.equipment))
            .where(Exercise.equipment.is_not(None), Exercise.external_id.is_not(None))
            .order_by(Exercise.equipment)
        )
        return [str(value) for value in rows.scalars().all() if value]

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        row = await self.session.execute(select(Exercise).where(Exercise.id == exercise_id))
        return row.scalar_one_or_none()

    async def upsert_many_from_external(
        self, items: list[dict[str, Any]], synced_at: datetime
    ) -> tuple[int, int]:
        external_ids = [str(item.get("id")) for item in items if item.get("id")]
        existing_map: dict[str, Exercise] = {}
        if external_ids:
            rows = await self.session.execute(
                select(Exercise).where(Exercise.external_id.in_(external_ids))
            )
            existing_map = {str(ex.external_id): ex for ex in rows.scalars().all() if ex.external_id}

        created = 0
        updated = 0
        for item in items:
            external_id = str(item.get("id") or "").strip()
            if not external_id:
                continue

            payload = {
                "name": str(item.get("name") or "").strip(),
                "body_part": (item.get("bodyPart") or None),
                "target": (item.get("target") or None),
                "equipment": (item.get("equipment") or None),
                "gif_url": (item.get("gifUrl") or None),
                "secondary_muscles": item.get("secondaryMuscles") or [],
                "instructions": item.get("instructions") or [],
                "synced_at": synced_at,
                "updated_at": synced_at,
            }
            if not payload["name"]:
                continue

            current = existing_map.get(external_id)
            if current:
                for key, value in payload.items():
                    setattr(current, key, value)
                self.session.add(current)
                updated += 1
            else:
                ex = Exercise(
                    external_id=external_id,
                    name=payload["name"],
                    body_part=payload["body_part"],
                    target=payload["target"],
                    equipment=payload["equipment"],
                    gif_url=payload["gif_url"],
                    secondary_muscles=payload["secondary_muscles"],
                    instructions=payload["instructions"],
                    synced_at=payload["synced_at"],
                    trainer_id=None,
                )
                self.session.add(ex)
                created += 1

        await self.session.commit()
        return created, updated

    async def add_favorite(self, user_id: UUID, exercise_id: UUID) -> ExerciseFavorite:
        row = await self.session.execute(
            select(ExerciseFavorite).where(
                ExerciseFavorite.user_id == user_id,
                ExerciseFavorite.exercise_id == exercise_id,
            )
        )
        favorite = row.scalar_one_or_none()
        if favorite:
            return favorite

        favorite = ExerciseFavorite(user_id=user_id, exercise_id=exercise_id)
        self.session.add(favorite)
        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def remove_favorite(self, user_id: UUID, exercise_id: UUID) -> bool:
        result = await self.session.execute(
            delete(ExerciseFavorite).where(
                ExerciseFavorite.user_id == user_id,
                ExerciseFavorite.exercise_id == exercise_id,
            )
        )
        await self.session.commit()
        return bool(result.rowcount and result.rowcount > 0)

    async def list_favorites(self, user_id: UUID) -> list[Exercise]:
        rows = await self.session.execute(
            select(Exercise)
            .join(ExerciseFavorite, ExerciseFavorite.exercise_id == Exercise.id)
            .where(ExerciseFavorite.user_id == user_id)
            .order_by(Exercise.name)
        )
        return list(rows.scalars().all())

    async def favorite_ids_for_user(self, user_id: UUID, exercise_ids: list[UUID]) -> set[UUID]:
        if not exercise_ids:
            return set()
        rows = await self.session.execute(
            select(ExerciseFavorite.exercise_id).where(
                ExerciseFavorite.user_id == user_id,
                ExerciseFavorite.exercise_id.in_(exercise_ids),
            )
        )
        return set(rows.scalars().all())

    async def find_existing_names(self, names: list[str]) -> set[str]:
        if not names:
            return set()
        lower_names = [n.strip().lower() for n in names]
        rows = await self.session.execute(
            select(func.lower(Exercise.name)).where(
                func.lower(Exercise.name).in_(lower_names)
            )
        )
        return set(rows.scalars().all())

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
