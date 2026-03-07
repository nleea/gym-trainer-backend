import uuid
from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.training_log import TrainingLog


class TrainerDashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_clients_with_names(self, trainer_id: uuid.UUID) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text("""
                SELECT c.id::text        AS client_id,
                       c.user_id::text   AS user_id,
                       c.status,
                       c.weight,
                       c.plan_id::text   AS plan_id,
                       c.nutrition_plan_id::text AS nutrition_plan_id,
                       u.name            AS user_name
                FROM clients c
                JOIN users u ON u.id = c.user_id
                WHERE c.trainer_id = :tid
                ORDER BY u.name
            """),
            {"tid": str(trainer_id)},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_recent_logs(self, trainer_id: uuid.UUID, days: int = 30) -> List[Any]:
        cutoff = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(
                TrainingLog.client_id,
                TrainingLog.date,
                TrainingLog.exercises,
                TrainingLog.duration,
            )
            .where(TrainingLog.trainer_id == trainer_id)
            .where(TrainingLog.date >= cutoff)
            .order_by(TrainingLog.date.desc())
        )
        return result.all()

    async def get_latest_metrics(self, client_ids: List[str]) -> List[Dict[str, Any]]:
        if not client_ids:
            return []
        result = await self.session.execute(
            text("""
                SELECT DISTINCT ON (client_id)
                    client_id::text AS client_id,
                    weight_kg,
                    date::text AS date
                FROM metrics
                WHERE client_id::text = ANY(:ids)
                ORDER BY client_id, date DESC
            """),
            {"ids": client_ids},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_prev_metrics(self, client_ids: List[str]) -> List[Dict[str, Any]]:
        if not client_ids:
            return []
        result = await self.session.execute(
            text("""
                WITH ranked AS (
                    SELECT client_id::text AS client_id, weight_kg,
                           ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date DESC) AS rn
                    FROM metrics
                    WHERE client_id::text = ANY(:ids)
                )
                SELECT client_id, weight_kg FROM ranked WHERE rn = 2
            """),
            {"ids": client_ids},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_weight_history(self, client_ids: List[str]) -> List[Dict[str, Any]]:
        if not client_ids:
            return []
        result = await self.session.execute(
            text("""
                WITH ranked AS (
                    SELECT client_id::text AS client_id, weight_kg, date::text AS date,
                           ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY date DESC) AS rn
                    FROM metrics
                    WHERE client_id::text = ANY(:ids)
                )
                SELECT client_id, weight_kg, date FROM ranked WHERE rn <= 8
                ORDER BY client_id, date ASC
            """),
            {"ids": client_ids},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_week_checkins(
        self, client_ids: List[str], week_start: date
    ) -> List[Dict[str, Any]]:
        if not client_ids:
            return []
        result = await self.session.execute(
            text("""
                SELECT client_id::text AS client_id,
                       mood, energy_level, stress_level, week_start::text AS week_start
                FROM weekly_checkins
                WHERE client_id::text = ANY(:ids)
                  AND week_start = :ws
            """),
            {"ids": client_ids, "ws": week_start},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_plan_names(self, plan_ids: List[str]) -> Dict[str, str]:
        if not plan_ids:
            return {}
        result = await self.session.execute(
            text("SELECT id::text AS id, name FROM training_plans WHERE id::text = ANY(:ids)"),
            {"ids": plan_ids},
        )
        return {row["id"]: row["name"] for row in result.mappings().all()}

    async def get_nutr_plan_names(self, plan_ids: List[str]) -> Dict[str, str]:
        if not plan_ids:
            return {}
        result = await self.session.execute(
            text("SELECT id::text AS id, name FROM nutrition_plans WHERE id::text = ANY(:ids)"),
            {"ids": plan_ids},
        )
        return {row["id"]: row["name"] for row in result.mappings().all()}

    async def get_latest_metric_dates(self, client_ids: List[str]) -> Dict[str, date]:
        """Return latest metric date per client (for no_metrics_2_weeks alert)."""
        if not client_ids:
            return {}
        result = await self.session.execute(
            text("""
                SELECT DISTINCT ON (client_id)
                    client_id::text AS client_id,
                    date
                FROM metrics
                WHERE client_id::text = ANY(:ids)
                ORDER BY client_id, date DESC
            """),
            {"ids": client_ids},
        )
        return {row["client_id"]: row["date"] for row in result.mappings().all()}

    async def get_attendance_rows(
        self, trainer_id: uuid.UUID, start: date, end: date
    ) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text(
                """
                SELECT a.client_id::text AS client_id,
                       a.date::text      AS date,
                       a.attended        AS attended
                FROM attendance a
                WHERE a.trainer_id = :tid
                  AND a.date BETWEEN :start AND :end
                """
            ),
            {"tid": trainer_id, "start": start, "end": end},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_training_logs_rows(
        self, trainer_id: uuid.UUID, start: date, end: date
    ) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text(
                """
                SELECT tl.client_id::text AS client_id,
                       tl.date::text      AS date,
                       tl.exercises       AS exercises
                FROM training_logs tl
                WHERE tl.trainer_id = :tid
                  AND tl.date BETWEEN :start AND :end
                """
            ),
            {"tid": trainer_id, "start": start, "end": end},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_training_logs_rows_before(
        self, trainer_id: uuid.UUID, before_date: date, days: int
    ) -> List[Dict[str, Any]]:
        start = before_date - timedelta(days=days)
        end = before_date - timedelta(days=1)
        return await self.get_training_logs_rows(trainer_id, start, end)

    async def get_meal_logs_rows(
        self, trainer_id: uuid.UUID, start: date, end: date
    ) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text(
                """
                SELECT ml.client_id::text AS client_id,
                       ml.date::text      AS date
                FROM meal_logs ml
                JOIN clients c ON c.id = ml.client_id
                WHERE c.trainer_id = :tid
                  AND ml.date BETWEEN :start AND :end
                """
            ),
            {"tid": trainer_id, "start": start, "end": end},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_weekly_checkins_rows(
        self, trainer_id: uuid.UUID, start: date, end: date
    ) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text(
                """
                SELECT wc.client_id::text AS client_id,
                       wc.week_start::text AS week_start,
                       wc.sleep_hours      AS sleep_hours,
                       wc.energy_level     AS energy_level,
                       wc.stress_level     AS stress_level,
                       wc.mood             AS mood
                FROM weekly_checkins wc
                WHERE wc.trainer_id = :tid
                  AND wc.week_start BETWEEN :start AND :end
                """
            ),
            {"tid": trainer_id, "start": start, "end": end},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_training_plan_weeks(self, plan_ids: List[str]) -> Dict[str, Any]:
        if not plan_ids:
            return {}
        result = await self.session.execute(
            text(
                """
                SELECT id::text AS id, weeks
                FROM training_plans
                WHERE id::text = ANY(:ids)
                """
            ),
            {"ids": plan_ids},
        )
        return {row["id"]: row["weeks"] for row in result.mappings().all()}
