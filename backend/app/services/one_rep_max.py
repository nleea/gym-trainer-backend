import uuid
from collections import defaultdict
from typing import List

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.schemas.one_rep_max import (
    ExerciseProgressItem,
    LoggedExerciseItem,
    OneRepMaxItem,
)
from app.schemas.rpe import RPEHistoryItem


def _estimate_1rm(weight: float, reps: int) -> float:
    """Return averaged Epley + Brzycki estimate. Epley-only for reps >= 37."""
    if reps <= 0 or weight <= 0:
        return 0.0
    if reps == 1:
        return weight
    epley = weight * (1 + reps / 30)
    if reps >= 37:
        return round(epley, 2)
    brzycki = weight * 36 / (37 - reps)
    return round((epley + brzycki) / 2, 2)


class OneRepMaxService:
    def __init__(
        self,
        training_logs_repo: TrainingLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.training_logs_repo = training_logs_repo
        self.clients_repo = clients_repo

    async def _assert_access(self, client_id: uuid.UUID, current_user: User):
        if current_user.role == "client":
            client = await self.clients_repo.get_by_user_id(current_user.id)
            if not client or client.id != client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )
        elif current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    # ── Logged exercises ───────────────────────────────────────────────────

    async def get_logged_exercises(
        self,
        client_id: uuid.UUID,
        current_user: User,
    ) -> List[LoggedExerciseItem]:
        await self._assert_access(client_id, current_user)

        rows = await self.training_logs_repo.get_logged_exercises(client_id)
        return [
            LoggedExerciseItem(
                exercise_id=r["exercise_id"],
                exercise_name=r["exercise_name"],
            )
            for r in rows
        ]

    # ── 1RM history ────────────────────────────────────────────────────────

    async def get_one_rep_max_history(
        self,
        client_id: uuid.UUID,
        exercise_id: str,
        current_user: User,
    ) -> List[OneRepMaxItem]:
        await self._assert_access(client_id, current_user)

        rows = await self.training_logs_repo.get_exercise_sets_history(
            client_id, exercise_id
        )
        if not rows:
            return []

        sessions = defaultdict(list)
        for r in rows:
            if not r["completed"]:
                continue
            sessions[r["date"]].append(r)

        history: List[OneRepMaxItem] = []
        for session_date in sorted(sessions.keys()):
            sets = sessions[session_date]
            est = max(_estimate_1rm(s["weight"], s["reps"]) for s in sets)
            if est <= 0:
                continue
            history.append(OneRepMaxItem(date=session_date, estimated_1rm=est))

        return history

    # ── Exercise progress ──────────────────────────────────────────────────

    async def get_exercise_progress(
        self,
        client_id: uuid.UUID,
        exercise_id: str,
        current_user: User,
    ) -> List[ExerciseProgressItem]:
        await self._assert_access(client_id, current_user)

        rows = await self.training_logs_repo.get_exercise_sets_history(
            client_id, exercise_id
        )
        if not rows:
            return []

        sessions = defaultdict(list)
        for r in rows:
            if not r["completed"]:
                continue
            sessions[r["date"]].append(r)

        progress: List[ExerciseProgressItem] = []
        for session_date in sorted(sessions.keys()):
            sets = sessions[session_date]
            max_weight = max(s["weight"] for s in sets)
            total_volume = sum(s["weight"] * s["reps"] for s in sets)
            if max_weight <= 0:
                continue
            progress.append(
                ExerciseProgressItem(
                    date=session_date,
                    max_weight=max_weight,
                    total_volume=round(total_volume, 2),
                )
            )

        return progress

    # ── RPE history ────────────────────────────────────────────────────────

    async def get_rpe_history(
        self,
        client_id: uuid.UUID,
        exercise_id: str,
        current_user: User,
    ) -> List[RPEHistoryItem]:
        await self._assert_access(client_id, current_user)

        rows = await self.training_logs_repo.get_rpe_history(client_id, exercise_id)
        return [
            RPEHistoryItem(date=r["date"], avg_rpe=r["avg_rpe"])
            for r in rows
        ]
