import uuid
from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status

from app.models.client import Client
from app.models.user import User
from app.repositories.interface.attendanceInterface import AttendanceRepositoryInterface
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.mealLogsInterface import MealLogsRepositoryInterface
from app.repositories.interface.metricsInterface import MetricsRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.schemas.client import (
    ClientCreate, ClientResponse, ClientSummaryResponse, ClientUpdate,
    WorkoutSummaryResponse, WorkoutSummaryStats, ExerciseProgressItem, WorkoutHistoryItem,
    WeeklyVolumeItem, HeatmapItem,
)
from app.schemas.training_log import _normalize_exercise


class ClientsService:
    def __init__(
        self,
        clients_repo: ClientsRepositoryInterface,
        metrics_repo: MetricsRepositoryInterface,
        attendance_repo: AttendanceRepositoryInterface,
        training_logs_repo: TrainingLogsRepositoryInterface,
        meal_logs_repo: MealLogsRepositoryInterface,
    ) -> None:
        self.clients_repo = clients_repo
        self.metrics_repo = metrics_repo
        self.attendance_repo = attendance_repo
        self.training_logs_repo = training_logs_repo
        self.meal_logs_repo = meal_logs_repo

    def _assert_trainer_owns_client(self, client: Client, trainer: User) -> None:
        if client.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_clients(self, trainer: User) -> List[Client]:
        return await self.clients_repo.list_by_trainer(trainer.id)

    async def get_client(self, client_id: uuid.UUID, trainer: User | None, requesting_client: User | None = None) -> Client:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if trainer:
            self._assert_trainer_owns_client(client, trainer)
        elif requesting_client:
            if client.user_id != requesting_client.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return client

    async def create_client(self, data: ClientCreate, trainer: User) -> Client:
        client = Client(
            user_id=data.user_id,
            trainer_id=trainer.id,
            status=data.status,
            start_date=data.start_date,
            goals=data.goals,
            weight=data.weight,
            height=data.height,
            age=data.age,
        )
        return await self.clients_repo.create(client)

    async def update_client(
        self, client_id: uuid.UUID, data: ClientUpdate, trainer: User
    ) -> Client:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        self._assert_trainer_owns_client(client, trainer)
        return await self.clients_repo.update(client, data.model_dump(exclude_none=True))

    async def get_client_summary(
        self, client_id: uuid.UUID, trainer: User | None, requesting_client: User | None = None
    ) -> ClientSummaryResponse:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if trainer:
            self._assert_trainer_owns_client(client, trainer)
        elif requesting_client:
            if client.user_id != requesting_client.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)

        all_metrics = await self.metrics_repo.list_by_client(client_id)
        latest_metric = all_metrics[0] if all_metrics else None
        latest_metrics_dict = None
        if latest_metric:
            latest_metrics_dict = {
                "date": str(latest_metric.date),
                "weight_kg": latest_metric.weight_kg,
                "body_fat_pct": latest_metric.body_fat_pct,
                "muscle_pct": latest_metric.muscle_pct,
            }

        all_attendance = await self.attendance_repo.list_by_client(client_id)
        recent_attendance = [a for a in all_attendance if a.date >= thirty_days_ago]
        attended_count = sum(1 for a in recent_attendance if a.attended)

        all_training_logs = await self.training_logs_repo.list_by_filters(client_id=client_id)
        recent_training_logs = [l for l in all_training_logs if l.date >= thirty_days_ago]

        all_meal_logs = await self.meal_logs_repo.list_by_filters(client_id=client_id)
        recent_meal_logs = [l for l in all_meal_logs if l.date >= seven_days_ago]

        return ClientSummaryResponse(
            client=ClientResponse.model_validate(client),
            latest_metrics=latest_metrics_dict,
            attendance_last_30_days=attended_count,
            attendance_total_last_30_days=len(recent_attendance),
            recent_training_logs_count=len(recent_training_logs),
            recent_meal_logs_count=len(recent_meal_logs),
        )

    async def get_workout_summary(
        self, client_id: uuid.UUID, current_user: User
    ) -> WorkoutSummaryResponse:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if current_user.role == "trainer":
            self._assert_trainer_owns_client(client, current_user)
        else:
            if client.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        logs = await self.training_logs_repo.list_by_filters(client_id=client_id)
        logs_sorted_desc = sorted(logs, key=lambda l: l.date, reverse=True)

        today = date.today()
        # Sunday-based week (matching frontend startOfWeek)
        week_start = today - timedelta(days=today.isoweekday() % 7)

        total_workouts = len(logs)
        weekly_workouts = sum(1 for l in logs if l.date >= week_start)
        total_minutes = sum(l.duration or 0 for l in logs)

        # Streak: consecutive days back from today (or yesterday if no workout today)
        workout_dates = {l.date for l in logs}
        base = today if today in workout_dates else today - timedelta(days=1)
        streak = 0
        for i in range(365):
            d = base - timedelta(days=i)
            if d in workout_dates:
                streak += 1
            else:
                break

        # Exercise progress (iterate chronologically to track prev session)
        ex_map: dict[str, dict] = {}
        for log in sorted(logs, key=lambda l: l.date):
            for raw_ex in (log.exercises or []):
                ex = _normalize_exercise(raw_ex) if isinstance(raw_ex, dict) else {}
                name = ex.get("exerciseName", "").strip()
                if not name:
                    continue
                sets = ex.get("sets", [])
                max_w = max((float(s.get("weight") or 0) for s in sets), default=0.0)

                if name not in ex_map:
                    ex_map[name] = {"best": 0.0, "last": None, "prev": None, "lastDate": None}
                row = ex_map[name]
                row["best"] = max(row["best"], max_w)
                if row["last"] is not None:
                    row["prev"] = row["last"]
                row["last"] = max_w
                row["lastDate"] = log.date

        exercise_progress: list[ExerciseProgressItem] = []
        for name, v in ex_map.items():
            last_w = v["last"] or 0.0
            prev_w = v["prev"] if v["prev"] is not None else last_w
            exercise_progress.append(ExerciseProgressItem(
                exerciseName=name,
                bestWeight=v["best"],
                lastWeight=last_w,
                lastDate=str(v["lastDate"]),
                trend=round(last_w - prev_w, 1),
            ))
        exercise_progress.sort(key=lambda e: e.lastDate, reverse=True)

        # Workout history with precomputed volume + maxWeight
        workout_history: list[WorkoutHistoryItem] = []
        for log in logs_sorted_desc:
            volume = 0.0
            max_weight = 0.0
            normalized_exercises = []
            for raw_ex in (log.exercises or []):
                ex = _normalize_exercise(raw_ex) if isinstance(raw_ex, dict) else {}
                sets = ex.get("sets", [])
                for s in sets:
                    w = float(s.get("weight") or 0)
                    r = float(s.get("reps") or 0)
                    volume += w * r
                    if w > max_weight:
                        max_weight = w
                normalized_exercises.append(ex)

            workout_history.append(WorkoutHistoryItem(
                id=str(log.id),
                date=str(log.date),
                duration=log.duration,
                notes=log.notes,
                effort=log.effort,
                exercises=normalized_exercises,
                volume=volume,
                maxWeight=max_weight,
            ))

        return WorkoutSummaryResponse(
            stats=WorkoutSummaryStats(
                totalWorkouts=total_workouts,
                weeklyWorkouts=weekly_workouts,
                totalMinutes=total_minutes,
                currentStreak=streak,
            ),
            exerciseProgress=exercise_progress,
            workoutHistory=workout_history,
        )

    async def get_weekly_volume(
        self, client_id: uuid.UUID, current_user: User
    ) -> list[WeeklyVolumeItem]:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if current_user.role == "trainer":
            self._assert_trainer_owns_client(client, current_user)
        else:
            if client.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        rows = await self.training_logs_repo.get_weekly_volume(client_id, weeks=12)
        return [WeeklyVolumeItem(week=r["week"], volume=r["volume"]) for r in rows]

    async def get_workout_heatmap(
        self, client_id: uuid.UUID, current_user: User
    ) -> list[HeatmapItem]:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if current_user.role == "trainer":
            self._assert_trainer_owns_client(client, current_user)
        else:
            if client.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        rows = await self.training_logs_repo.get_workout_heatmap(client_id)
        return [HeatmapItem(date=r["date"], count=r["count"], volume=r["volume"]) for r in rows]
