import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.training_log import TrainingLog
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface

_WEEKLY_VOLUME_SQL = text("""
WITH
  week_series AS (
    SELECT generate_series(
      date_trunc('week', CURRENT_DATE) - ((:weeks - 1) || ' weeks')::interval,
      date_trunc('week', CURRENT_DATE),
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
      AND tl.date >= (date_trunc('week', CURRENT_DATE) - ((:weeks - 1) || ' weeks')::interval)::date
  )
SELECT
  w.week_start::text AS week,
  ROUND(COALESCE(SUM(lv.log_volume), 0)) AS volume
FROM week_series w
LEFT JOIN log_volumes lv ON lv.week_start = w.week_start
GROUP BY w.week_start
ORDER BY w.week_start ASC
""")

_LAST_PERF_SQL = text("""
SELECT DISTINCT ON (ex->>'exerciseId')
  ex->>'exerciseId' AS exercise_id,
  tl.date::text     AS date,
  ex->'sets'        AS sets
FROM training_logs tl,
  jsonb_array_elements(
    CASE WHEN jsonb_typeof(tl.exercises::jsonb) = 'array'
         THEN tl.exercises::jsonb ELSE '[]'::jsonb END
  ) ex
WHERE tl.client_id = :cid
  AND ex->>'exerciseId' = ANY(:exercise_ids)
ORDER BY ex->>'exerciseId', tl.date DESC
""")

_MAX_WEIGHTS_SQL = text("""
SELECT
  ex->>'exerciseId' AS exercise_id,
  MAX((s->>'weight')::float) AS max_weight
FROM training_logs tl,
  jsonb_array_elements(
    CASE WHEN jsonb_typeof(tl.exercises::jsonb) = 'array'
         THEN tl.exercises::jsonb ELSE '[]'::jsonb END
  ) ex,
  jsonb_array_elements(
    CASE WHEN jsonb_typeof(ex->'sets') = 'array'
         THEN ex->'sets' ELSE '[]'::jsonb END
  ) s
WHERE tl.client_id = :cid
  AND tl.date < :log_date
  AND (s->>'weight') IS NOT NULL
GROUP BY ex->>'exerciseId'
""")

_HEATMAP_SQL = text("""
SELECT
  tl.date::text AS date,
  COUNT(*) AS count,
  ROUND(COALESCE(SUM(
    (SELECT COALESCE(SUM(COALESCE((s->>'reps')::float, 0) * COALESCE((s->>'weight')::float, 0)), 0)
     FROM jsonb_array_elements(
       CASE WHEN jsonb_typeof(tl.exercises::jsonb) = 'array' THEN tl.exercises::jsonb ELSE '[]'::jsonb END
     ) ex,
     jsonb_array_elements(
       CASE WHEN jsonb_typeof(ex->'sets') = 'array' THEN ex->'sets' ELSE '[]'::jsonb END
     ) s)
  ), 0)) AS volume
FROM training_logs tl
WHERE tl.client_id = :cid
  AND tl.date >= (CURRENT_DATE - INTERVAL '12 months')::date
GROUP BY tl.date
ORDER BY tl.date ASC
""")


_VOLUME_BY_RANGE_SQL = text("""
WITH
  week_series AS (
    SELECT generate_series(
      date_trunc('week', :from_date::date),
      date_trunc('week', :to_date::date),
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
      AND tl.date >= :from_date
      AND tl.date <= :to_date
  )
SELECT
  w.week_start::text AS week,
  ROUND(COALESCE(SUM(lv.log_volume), 0)) AS volume
FROM week_series w
LEFT JOIN log_volumes lv ON lv.week_start = w.week_start
GROUP BY w.week_start
ORDER BY w.week_start ASC
""")

_COUNT_LOGS_RANGE_SQL = text("""
SELECT COUNT(*) AS cnt
FROM training_logs
WHERE client_id = :cid
  AND date >= :from_date
  AND date <= :to_date
""")


class TrainingLogsRepository(TrainingLogsRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_filters(
        self,
        client_id: Optional[uuid.UUID] = None,
        week_start: Optional[date] = None,
    ) -> List[TrainingLog]:
        query = select(TrainingLog)
        if client_id:
            query = query.where(TrainingLog.client_id == client_id)
        if week_start:
            week_end = week_start + timedelta(days=6)
            query = query.where(
                TrainingLog.date >= week_start,
                TrainingLog.date <= week_end,
            )
        result = await self.session.execute(query.order_by(TrainingLog.date.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, log_id: uuid.UUID) -> TrainingLog | None:
        result = await self.session.execute(
            select(TrainingLog).where(TrainingLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_and_date(self, client_id: uuid.UUID, log_date: date) -> TrainingLog | None:
        result = await self.session.execute(
            select(TrainingLog).where(
                TrainingLog.client_id == client_id,
                TrainingLog.date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_client_week(self, client_id: uuid.UUID, week_start: date) -> List[TrainingLog]:
        week_end = week_start + timedelta(days=6)
        result = await self.session.execute(
            select(TrainingLog).where(
                TrainingLog.client_id == client_id,
                TrainingLog.date >= week_start,
                TrainingLog.date <= week_end,
            ).order_by(TrainingLog.date)
        )
        return list(result.scalars().all())

    async def create(self, log: TrainingLog) -> TrainingLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def update(self, log: TrainingLog, data: dict) -> TrainingLog:
        for key, value in data.items():
            if value is not None:
                setattr(log, key, value)
        log.updated_at = datetime.utcnow()
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def upsert_by_client_date(self, log: TrainingLog) -> TrainingLog:
        """Atomic INSERT ON CONFLICT (client_id, date) DO UPDATE."""
        now = datetime.utcnow()
        stmt = pg_insert(TrainingLog).values(
            id=log.id,
            client_id=log.client_id,
            trainer_id=log.trainer_id,
            date=log.date,
            exercises=log.exercises,
            duration=log.duration,
            notes=log.notes,
            effort=log.effort,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_training_logs_client_date",
            set_={
                "exercises": stmt.excluded.exercises,
                "duration": stmt.excluded.duration,
                "notes": stmt.excluded.notes,
                "effort": stmt.excluded.effort,
                "updated_at": now,
            },
        )
        stmt = stmt.returning(TrainingLog)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def get_weekly_volume(self, client_id: uuid.UUID, weeks: int = 12) -> List[Dict[str, Any]]:
        rows = (await self.session.execute(
            _WEEKLY_VOLUME_SQL, {"cid": client_id, "weeks": weeks}
        )).mappings().all()
        return [{"week": row["week"], "volume": float(row["volume"])} for row in rows]

    async def get_workout_heatmap(self, client_id: uuid.UUID) -> List[Dict[str, Any]]:
        rows = (await self.session.execute(
            _HEATMAP_SQL, {"cid": client_id}
        )).mappings().all()
        return [{"date": row["date"], "count": int(row["count"]), "volume": float(row["volume"])} for row in rows]

    async def get_last_performance(self, client_id: uuid.UUID, exercise_ids: List[str]) -> List[Dict[str, Any]]:
        if not exercise_ids:
            return []
        rows = (await self.session.execute(
            _LAST_PERF_SQL, {"cid": client_id, "exercise_ids": exercise_ids}
        )).mappings().all()
        result = []
        for row in rows:
            sets = row["sets"] or []
            if isinstance(sets, str):
                import json
                sets = json.loads(sets)
            best = max(
                ((float(s.get("weight") or 0), int(s.get("reps") or 0)) for s in sets),
                default=(0.0, 0),
            )
            result.append({
                "exercise_id": row["exercise_id"],
                "date": row["date"],
                "weight": best[0],
                "reps": best[1],
            })
        return result

    async def get_max_weights_before_date(self, client_id: uuid.UUID, log_date: date) -> Dict[str, float]:
        rows = (await self.session.execute(
            _MAX_WEIGHTS_SQL, {"cid": client_id, "log_date": log_date}
        )).mappings().all()
        return {row["exercise_id"]: float(row["max_weight"]) for row in rows}

    async def get_volume_by_date_range(
        self, client_id: uuid.UUID, from_date: date, to_date: date,
    ) -> List[Dict[str, Any]]:
        rows = (await self.session.execute(
            _VOLUME_BY_RANGE_SQL, {"cid": client_id, "from_date": from_date, "to_date": to_date}
        )).mappings().all()
        return [{"week": row["week"], "volume": float(row["volume"])} for row in rows]

    async def count_logs_in_range(
        self, client_id: uuid.UUID, from_date: date, to_date: date,
    ) -> int:
        row = (await self.session.execute(
            _COUNT_LOGS_RANGE_SQL, {"cid": client_id, "from_date": from_date, "to_date": to_date}
        )).mappings().first()
        return int(row["cnt"]) if row else 0
