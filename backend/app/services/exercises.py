import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface
from app.models.exercise import Exercise
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseSyncResponse,
    ExerciseUpdate,
)

EXERCISEDB_URL = "https://exercisedb.p.rapidapi.com/exercises?limit=1300&offset=0"
EXERCISEDB_HOST = "exercisedb.p.rapidapi.com"


class ExercisesService:
    def __init__(self, exercises_repo: ExercisesRepositoryInterface) -> None:
        self.exercises_repo = exercises_repo

    async def list_exercises(
        self,
        *,
        current_user: User,
        body_part: Optional[str] = None,
        equipment: Optional[str] = None,
        q: Optional[str] = None,
        favorites_only: bool = False,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ExerciseListResponse:
        target_user = self._resolve_target_user(current_user, user_id)
        exercises, total = await self.exercises_repo.list_exercises(
            body_part=body_part,
            equipment=equipment,
            q=q,
            favorites_only=favorites_only,
            user_id=target_user if favorites_only else None,
            limit=limit,
            offset=offset,
        )
        return ExerciseListResponse(
            items=await self._map_with_favorites(exercises, target_user),
            total=total,
            limit=limit,
            offset=offset,
        )

    async def search_exercises(self, q: str, current_user: User, limit: int = 20) -> list[ExerciseResponse]:
        target_user = current_user.id
        exercises = await self.exercises_repo.search_by_name(q=q, limit=limit)
        return await self._map_with_favorites(exercises, target_user)

    async def list_body_parts(self) -> list[str]:
        return await self.exercises_repo.list_body_parts()

    async def list_equipment(self) -> list[str]:
        return await self.exercises_repo.list_equipment()

    async def sync_exercises(self, current_user: User) -> ExerciseSyncResponse:
        if current_user.role not in {"trainer", "admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        key = settings.RAPIDAPI_KEY
        if not key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RAPIDAPI_KEY is not configured",
            )

        data = self._fetch_from_exercise_db(key)
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from ExerciseDB",
            )

        synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
        created, updated = await self.exercises_repo.upsert_many_from_external(data, synced_at)
        return ExerciseSyncResponse(
            synced_count=created + updated,
            created_count=created,
            updated_count=updated,
            synced_at=synced_at,
        )

    async def add_favorite(self, current_user: User, exercise_id: uuid.UUID):
        exercise = await self.exercises_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        return await self.exercises_repo.add_favorite(current_user.id, exercise_id)

    async def remove_favorite(self, current_user: User, exercise_id: uuid.UUID):
        removed = await self.exercises_repo.remove_favorite(current_user.id, exercise_id)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")

    async def list_favorites(self, current_user: User, user_id: Optional[uuid.UUID] = None) -> list[ExerciseResponse]:
        target_user = self._resolve_target_user(current_user, user_id)
        rows = await self.exercises_repo.list_favorites(target_user)
        return await self._map_with_favorites(rows, target_user)

    async def create_custom(self, data: ExerciseCreate, current_user: User) -> Exercise:
        exercise = Exercise(
            name=data.name,
            muscle_group=data.muscle_group,
            description=data.description,
            trainer_id=current_user.id,
        )
        return await self.exercises_repo.create(exercise)

    async def update_custom(
        self, exercise_id: uuid.UUID, data: ExerciseUpdate, current_user: User
    ) -> Exercise:
        exercise = await self.exercises_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        if exercise.trainer_id and exercise.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await self.exercises_repo.update(exercise, data.model_dump(exclude_none=True))

    async def delete_custom(self, exercise_id: uuid.UUID, current_user: User) -> None:
        exercise = await self.exercises_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        if exercise.trainer_id and exercise.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await self.exercises_repo.delete(exercise)

    def _resolve_target_user(self, current_user: User, user_id: Optional[uuid.UUID]) -> uuid.UUID:
        if user_id and user_id != current_user.id and current_user.role not in {"trainer", "admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return user_id or current_user.id

    async def _map_with_favorites(
        self, exercises: list, user_id: Optional[uuid.UUID]
    ) -> list[ExerciseResponse]:
        favorite_ids: set[uuid.UUID] = set()
        if user_id:
            favorite_ids = await self.exercises_repo.favorite_ids_for_user(
                user_id, [exercise.id for exercise in exercises]
            )
        return [
            ExerciseResponse.model_validate(
                {
                    **exercise.model_dump(),
                    "secondary_muscles": exercise.secondary_muscles or [],
                    "instructions": exercise.instructions or [],
                    "is_favorite": exercise.id in favorite_ids,
                }
            )
            for exercise in exercises
        ]

    def _fetch_from_exercise_db(self, api_key: str):
        req = Request(
            EXERCISEDB_URL,
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": EXERCISEDB_HOST,
            },
            method="GET",
        )
        try:
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ExerciseDB error: {exc.code}",
            ) from exc
        except URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to connect to ExerciseDB",
            ) from exc
