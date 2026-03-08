"""
Monthly report data aggregation service.
Queries all data for a given client+month and assembles the report dict.
"""

import uuid
from calendar import monthrange
from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.client import Client
from app.models.metric import Metric
from app.models.monthly_report import MonthlyReport
from app.models.user import User
from app.models.weekly_checkin import WeeklyCheckin
from app.repositories.implementations.postgres.monthly_report import MonthlyReportRepository
from app.schemas.training_log import _normalize_exercise


# ── SQL helpers ───────────────────────────────────────────────────────────────

_WEEKLY_VOLUME_MONTH_SQL = text("""
WITH
  week_series AS (
    SELECT generate_series(
      date_trunc('week', CAST(:start_date AS date)),
      date_trunc('week', CAST(:end_date AS date)),
      '1 week'::interval
    )::date AS week_start
  ),
  log_volumes AS (
    SELECT
      date_trunc('week', tl.date)::date AS week_start,
      COALESCE(
        (SELECT SUM(
            COALESCE((s->>'reps')::float, 0) * COALESCE((s->>'weight')::float, 0)
          )
          FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(tl.exercises::jsonb) = 'array'
                 THEN tl.exercises::jsonb ELSE '[]'::jsonb END
          ) ex,
          jsonb_array_elements(
            CASE WHEN jsonb_typeof(ex->'sets') = 'array'
                 THEN ex->'sets' ELSE '[]'::jsonb END
          ) s
        ), 0
      ) AS log_volume
    FROM training_logs tl
    WHERE tl.client_id = :cid
      AND tl.date BETWEEN :start_date AND :end_date
  )
SELECT
  w.week_start::text AS week,
  ROUND(COALESCE(SUM(lv.log_volume), 0)) AS volume
FROM week_series w
LEFT JOIN log_volumes lv ON lv.week_start = w.week_start
GROUP BY w.week_start
ORDER BY w.week_start ASC
""")


class ReportService:

    async def get_monthly_data(
        self,
        client_id: uuid.UUID,
        month: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Aggregate all data for a client for the given month (format: YYYY-MM)."""
        year, mon = int(month.split("-")[0]), int(month.split("-")[1])
        days_in_month = monthrange(year, mon)[1]
        start_date = date(year, mon, 1)
        end_date = date(year, mon, days_in_month)

        # ── Load client + users ───────────────────────────────────────────────
        client_row = (await db.execute(select(Client).where(Client.id == client_id))).scalar_one_or_none()
        if not client_row:
            raise ValueError(f"Client {client_id} not found")

        client_user = (await db.execute(select(User).where(User.id == client_row.user_id))).scalar_one_or_none()
        trainer_user = (await db.execute(select(User).where(User.id == client_row.trainer_id))).scalar_one_or_none()

        # ── Training logs ─────────────────────────────────────────────────────
        from app.models.training_log import TrainingLog
        logs_result = await db.execute(
            select(TrainingLog)
            .where(TrainingLog.client_id == client_id)
            .where(TrainingLog.date >= start_date)
            .where(TrainingLog.date <= end_date)
            .order_by(TrainingLog.date)
        )
        logs = list(logs_result.scalars().all())

        workout_summary = self._build_workout_summary(logs, start_date, end_date, days_in_month)
        exercise_progress = self._build_exercise_progress(logs)

        # ── Weekly volume (SQL) ───────────────────────────────────────────────
        vol_rows = (await db.execute(
            _WEEKLY_VOLUME_MONTH_SQL,
            {"cid": client_id, "start_date": start_date, "end_date": end_date},
        )).mappings().all()
        weekly_volume = [
            {"week": row["week"], "volume": float(row["volume"])}
            for row in vol_rows
        ]

        # ── PRs (computed in Python from logs) ────────────────────────────────
        prs = self._build_prs_from_logs(logs)

        # ── Body metrics ──────────────────────────────────────────────────────
        metrics_result = await db.execute(
            select(Metric)
            .where(Metric.client_id == client_id)
            .where(Metric.date >= start_date)
            .where(Metric.date <= end_date)
            .order_by(Metric.date)
        )
        metrics = list(metrics_result.scalars().all())
        body_metrics = self._build_body_metrics(metrics)

        # ── Exercise progress (vs previous month) ─────────────────────────────
        prev_month_end = start_date - timedelta(days=1)
        prev_month_start = date(prev_month_end.year, prev_month_end.month, 1)
        prev_logs_result = await db.execute(
            select(TrainingLog)
            .where(TrainingLog.client_id == client_id)
            .where(TrainingLog.date >= prev_month_start)
            .where(TrainingLog.date <= prev_month_end)
        )
        prev_logs = list(prev_logs_result.scalars().all())
        exercise_progress = self._build_exercise_progress(logs, prev_logs)

        # ── Nutrition adherence ───────────────────────────────────────────────
        from app.models.meal_log import MealLog
        meal_logs_result = await db.execute(
            select(MealLog)
            .where(MealLog.client_id == client_id)
            .where(MealLog.date >= start_date)
            .where(MealLog.date <= end_date)
        )
        meal_logs = list(meal_logs_result.scalars().all())
        nutrition_adherence = self._build_nutrition_adherence(meal_logs, days_in_month)

        # ── Weekly checkins ───────────────────────────────────────────────────
        checkins_result = await db.execute(
            select(WeeklyCheckin)
            .where(WeeklyCheckin.client_id == client_id)
            .where(WeeklyCheckin.week_start >= start_date)
            .where(WeeklyCheckin.week_start <= end_date)
            .order_by(WeeklyCheckin.week_start)
        )
        checkins_raw = list(checkins_result.scalars().all())
        checkins = [
            {
                "weekStart": str(c.week_start),
                "sleepHours": c.sleep_hours,
                "energyLevel": c.energy_level,
                "stressLevel": c.stress_level,
                "mood": c.mood,
            }
            for c in checkins_raw
        ]

        # ── Assemble ──────────────────────────────────────────────────────────
        month_name = start_date.strftime("%B %Y")
        return {
            "client": {
                "name": client_user.name if client_user else "—",
                "email": client_user.email if client_user else "—",
                "trainerName": trainer_user.name if trainer_user else "—",
            },
            "period": {
                "month": month_name,
                "startDate": str(start_date),
                "endDate": str(end_date),
            },
            "workoutSummary": workout_summary,
            "weeklyVolume": weekly_volume,
            "prs": prs,
            "bodyMetrics": body_metrics,
            "exerciseProgress": exercise_progress,
            "nutritionAdherence": nutrition_adherence,
            "checkins": checkins,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_workout_summary(
        self, logs, start_date: date, end_date: date, days_in_month: int
    ) -> Dict[str, Any]:
        total_workouts = len(logs)
        total_minutes = sum(l.duration or 0 for l in logs)
        total_volume = 0.0
        for log in logs:
            for raw_ex in (log.exercises or []):
                ex = _normalize_exercise(raw_ex) if isinstance(raw_ex, dict) else {}
                for s in ex.get("sets", []):
                    total_volume += float(s.get("weight") or 0) * float(s.get("reps") or 0)

        # Best streak within the month
        workout_dates = {l.date for l in logs}
        best_streak = 0
        current_streak = 0
        d = start_date
        while d <= end_date:
            if d in workout_dates:
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0
            d += timedelta(days=1)

        # Planned workouts: approximate as working days (Mon-Fri) — or just total_days/7*5
        planned = round(days_in_month / 7 * 5)
        adherence_pct = round(total_workouts / planned * 100) if planned else 0

        return {
            "totalWorkouts": total_workouts,
            "plannedWorkouts": planned,
            "adherencePct": min(adherence_pct, 100),
            "totalVolumeKg": round(total_volume),
            "bestStreak": best_streak,
            "totalMinutes": total_minutes,
        }

    def _build_exercise_progress(self, logs, prev_logs=None) -> list:
        """Top 5 exercises by session count with start/end weight comparison."""
        # Current month: first and last max weight per exercise
        ex_first: Dict[str, float] = {}
        ex_last: Dict[str, float] = {}
        ex_sessions: Dict[str, int] = {}

        for log in sorted(logs, key=lambda l: l.date):
            seen_in_log: set = set()
            for raw_ex in (log.exercises or []):
                ex = _normalize_exercise(raw_ex) if isinstance(raw_ex, dict) else {}
                name = ex.get("exerciseName", "").strip()
                if not name:
                    continue
                sets = ex.get("sets", [])
                max_w = max((float(s.get("weight") or 0) for s in sets), default=0.0)
                if name not in ex_first:
                    ex_first[name] = max_w
                ex_last[name] = max_w
                if name not in seen_in_log:
                    ex_sessions[name] = ex_sessions.get(name, 0) + 1
                    seen_in_log.add(name)

        # Sort by sessions desc, take top 5
        top5 = sorted(ex_sessions.keys(), key=lambda n: ex_sessions[n], reverse=True)[:5]
        return [
            {
                "exerciseName": name,
                "startWeight": ex_first.get(name, 0),
                "endWeight": ex_last.get(name, 0),
                "change": round(ex_last.get(name, 0) - ex_first.get(name, 0), 1),
                "totalSessions": ex_sessions[name],
            }
            for name in top5
        ]

    def _build_prs_from_logs(self, logs) -> list:
        """Personal records: exercises where end weight > start weight in the month."""
        ex_first: Dict[str, tuple] = {}  # name → (weight, date)
        ex_best: Dict[str, tuple] = {}   # name → (weight, date)

        for log in sorted(logs, key=lambda l: l.date):
            for raw_ex in (log.exercises or []):
                ex = _normalize_exercise(raw_ex) if isinstance(raw_ex, dict) else {}
                name = ex.get("exerciseName", "").strip()
                if not name:
                    continue
                sets = ex.get("sets", [])
                max_w = max((float(s.get("weight") or 0) for s in sets), default=0.0)
                if max_w == 0:
                    continue
                if name not in ex_first:
                    ex_first[name] = (max_w, log.date)
                if name not in ex_best or max_w > ex_best[name][0]:
                    ex_best[name] = (max_w, log.date)

        prs = []
        for name, (best_w, best_date) in ex_best.items():
            first_w = ex_first[name][0]
            if best_w > first_w:
                prs.append({
                    "exerciseName": name,
                    "newWeight": best_w,
                    "previousBest": first_w,
                    "date": str(best_date),
                })
        return sorted(prs, key=lambda p: p["date"], reverse=True)

    def _build_body_metrics(self, metrics) -> Dict[str, Any]:
        def metric_delta(values):
            if not values:
                return None
            start = values[0]
            end = values[-1]
            return {"start": start, "end": end, "change": round(end - start, 2)}

        weights = [m.weight_kg for m in metrics if m.weight_kg is not None]
        body_fat = [m.body_fat_pct for m in metrics if m.body_fat_pct is not None]
        waist = [m.waist_cm for m in metrics if m.waist_cm is not None]

        return {
            "weight": metric_delta(weights),
            "bodyFatPct": metric_delta(body_fat),
            "waistCm": metric_delta(waist),
        }

    def _build_nutrition_adherence(self, meal_logs, days_in_month: int) -> Dict[str, Any]:
        meal_only = [l for l in meal_logs if l.meal_key != "daily_water"]
        days_logged = len({l.date for l in meal_only})
        calories_list = [l.calories for l in meal_only if l.calories]
        protein_list = [l.protein for l in meal_only if l.protein]

        return {
            "daysLogged": days_logged,
            "totalDays": days_in_month,
            "adherencePct": round(days_logged / days_in_month * 100) if days_in_month else 0,
            "avgCalories": round(sum(calories_list) / len(calories_list)) if calories_list else 0,
            "avgProtein": round(sum(protein_list) / len(protein_list), 1) if protein_list else 0,
        }

    # ── R2 upload ─────────────────────────────────────────────────────────────

    async def upload_to_r2(self, pdf_buffer, client_id: uuid.UUID, month: str) -> Optional[str]:
        """Upload PDF buffer to Cloudflare R2. Returns public URL or None if not configured."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            import boto3
            from app.core.config import settings

            if not all([settings.R2_ACCESS_KEY_ID, settings.R2_SECRET_ACCESS_KEY, settings.R2_BUCKET_NAME]):
                logger.warning("R2 not configured — skipping upload")
                return None

            endpoint = (
                settings.R2_ENDPOINT_URL.rstrip("/")
                if settings.R2_ENDPOINT_URL
                else f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            )
            key = f"reports/{client_id}/report_{month}.pdf"
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
            pdf_buffer.seek(0)
            s3.put_object(
                Bucket=str(settings.R2_BUCKET_NAME),
                Key=key,
                Body=pdf_buffer.read(),
                ContentType="application/pdf",
            )
            public_base = (
                settings.R2_PUBLIC_BASE_URL.rstrip("/")
                if settings.R2_PUBLIC_BASE_URL
                else f"{endpoint}/{settings.R2_BUCKET_NAME}"
            )
            return f"{public_base}/{key}"
        except Exception as e:
            logger.error(f"R2 upload failed: {e}")
            return None

    # ── DB record helpers ─────────────────────────────────────────────────────

    async def save_report_record(
        self,
        client_id: uuid.UUID,
        month: str,
        pdf_url: Optional[str],
        generated_by: str,
        db: AsyncSession,
    ) -> MonthlyReport:
        repo = MonthlyReportRepository(db)
        report = MonthlyReport(
            client_id=client_id,
            month=month,
            pdf_url=pdf_url,
            generated_by=generated_by,
        )
        return await repo.create(report)

    async def list_reports(self, client_id: uuid.UUID, db: AsyncSession):
        repo = MonthlyReportRepository(db)
        return await repo.list_by_client(client_id)
