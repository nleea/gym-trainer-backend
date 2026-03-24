import uuid
from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.mealLogsInterface import MealLogsRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.repositories.interface.trainingPlansInterface import TrainingPlansRepositoryInterface
from app.schemas.volume_metrics import (
    AdherenceBlock,
    AdherenceResponse,
    VolumeResponse,
    WeeklyVolume,
)


class VolumeMetricsService:
    def __init__(
        self,
        training_logs_repo: TrainingLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
        training_plans_repo: TrainingPlansRepositoryInterface,
        meal_logs_repo: MealLogsRepositoryInterface,
    ) -> None:
        self.training_logs_repo = training_logs_repo
        self.clients_repo = clients_repo
        self.training_plans_repo = training_plans_repo
        self.meal_logs_repo = meal_logs_repo

    async def _assert_access(self, client_id: uuid.UUID, current_user: User):
        if current_user.role == "client":
            client = await self.clients_repo.get_by_user_id(current_user.id)
            if not client or client.id != client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )
            return client
        elif current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )
            return client
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # ── Volume ────────────────────────────────────────────────────────────────

    async def get_weekly_volume(
        self,
        client_id: uuid.UUID,
        from_date: date,
        to_date: date,
        current_user: User,
    ) -> VolumeResponse:
        await self._assert_access(client_id, current_user)

        rows = await self.training_logs_repo.get_volume_by_date_range(
            client_id, from_date, to_date
        )

        weeks = [WeeklyVolume(week=r["week"], volume=r["volume"]) for r in rows]
        total = sum(w.volume for w in weeks)

        return VolumeResponse(weeks=weeks, total_volume=total)

    # ── Adherence ─────────────────────────────────────────────────────────────

    async def get_adherence_rate(
        self,
        client_id: uuid.UUID,
        from_date: date,
        to_date: date,
        current_user: User,
    ) -> AdherenceResponse:
        client = await self._assert_access(client_id, current_user)

        # ── Training adherence ────────────────────────────────────────────
        completed_workouts = await self.training_logs_repo.count_logs_in_range(
            client_id, from_date, to_date
        )
        planned_workouts = await self._count_planned_training_days(
            client, from_date, to_date
        )
        training_pct = (
            round(completed_workouts / planned_workouts * 100, 1)
            if planned_workouts > 0
            else 0.0
        )

        # ── Nutrition adherence ───────────────────────────────────────────
        meal_logs = await self.meal_logs_repo.list_by_filters(
            client_id=client_id, start_date=from_date, end_date=to_date
        )
        days_with_meals = len({
            log.date for log in meal_logs if log.meal_key != "daily_water"
        })
        total_days = (to_date - from_date).days + 1
        nutrition_pct = round(days_with_meals / total_days * 100, 1) if total_days > 0 else 0.0

        return AdherenceResponse(
            training=AdherenceBlock(
                completed=completed_workouts,
                planned=planned_workouts,
                percentage=training_pct,
            ),
            nutrition=AdherenceBlock(
                completed=days_with_meals,
                planned=total_days,
                percentage=nutrition_pct,
            ),
        )

    async def _count_planned_training_days(
        self, client, from_date: date, to_date: date
    ) -> int:
        """Count planned workout days from the training plan within the range.

        The plan's `weeks` JSON is a list of week objects, each containing `days`
        (a list of day objects). A day counts as a planned workout if it has a
        non-empty `exercises` list. The plan cycles through its weeks starting
        from the client's start_date (or assigned_at).
        """
        if not client.plan_id:
            return 0

        plan = await self.training_plans_repo.get_by_id(client.plan_id)
        if not plan or not plan.weeks:
            return 0

        weeks_data = plan.weeks
        if not isinstance(weeks_data, list) or len(weeks_data) == 0:
            return 0

        # Count training days per week in the plan cycle
        training_days_per_week: List[int] = []
        for week in weeks_data:
            if not isinstance(week, dict):
                training_days_per_week.append(0)
                continue
            days = week.get("days", [])
            if not isinstance(days, list):
                training_days_per_week.append(0)
                continue
            count = sum(
                1
                for day in days
                if isinstance(day, dict)
                and isinstance(day.get("exercises"), list)
                and len(day["exercises"]) > 0
            )
            training_days_per_week.append(count)

        if not any(training_days_per_week):
            return 0

        # Determine plan cycle start
        plan_start = client.start_date or (
            plan.assigned_at.date() if plan.assigned_at else from_date
        )

        # Count planned training days within the range
        cycle_len = len(training_days_per_week)

        planned = 0
        # Walk week by week through the range
        current = from_date
        while current <= to_date:
            week_end = min(current + timedelta(days=6), to_date)
            # Determine which plan week this falls on
            days_since_start = (current - plan_start).days
            if days_since_start < 0:
                # Before the plan started, no planned workouts
                current = week_end + timedelta(days=1)
                continue
            week_index = (days_since_start // 7) % cycle_len
            planned += training_days_per_week[week_index]
            current = week_end + timedelta(days=1)

        return planned
