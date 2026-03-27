import uuid
from datetime import date, datetime
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.metric import Metric
from app.repositories.interface.metricsInterface import MetricsRepositoryInterface

_DELTA_SQL = text("""
WITH
  rw  AS (SELECT weight_kg,   date, ROW_NUMBER() OVER (ORDER BY date DESC) rn FROM metrics WHERE client_id = :cid AND weight_kg   IS NOT NULL),
  rf  AS (SELECT body_fat_pct,date, ROW_NUMBER() OVER (ORDER BY date DESC) rn FROM metrics WHERE client_id = :cid AND body_fat_pct IS NOT NULL),
  rwc AS (SELECT waist_cm,    date, ROW_NUMBER() OVER (ORDER BY date DESC) rn FROM metrics WHERE client_id = :cid AND waist_cm    IS NOT NULL),
  rab AS (SELECT abdomen_cm,  date, ROW_NUMBER() OVER (ORDER BY date DESC) rn FROM metrics WHERE client_id = :cid AND abdomen_cm  IS NOT NULL)
SELECT
  (SELECT weight_kg    FROM rw  WHERE rn=1) w_last,  (SELECT weight_kg    FROM rw  WHERE rn=2) w_prev,
  (SELECT body_fat_pct FROM rf  WHERE rn=1) f_last,  (SELECT body_fat_pct FROM rf  WHERE rn=2) f_prev,
  (SELECT waist_cm     FROM rwc WHERE rn=1) wc_last, (SELECT waist_cm     FROM rwc WHERE rn=2) wc_prev,
  (SELECT abdomen_cm   FROM rab WHERE rn=1) ab_last, (SELECT abdomen_cm   FROM rab WHERE rn=2) ab_prev
""")

_SERIES_SQL = text("""
SELECT 'weightKg'   AS field, date::text AS date, weight_kg    AS value FROM (SELECT date, weight_kg    FROM metrics WHERE client_id=:cid AND weight_kg    IS NOT NULL ORDER BY date DESC LIMIT 6) s
UNION ALL
SELECT 'bodyFatPct' AS field, date::text AS date, body_fat_pct AS value FROM (SELECT date, body_fat_pct FROM metrics WHERE client_id=:cid AND body_fat_pct IS NOT NULL ORDER BY date DESC LIMIT 6) s
UNION ALL
SELECT 'waistCm'    AS field, date::text AS date, waist_cm     AS value FROM (SELECT date, waist_cm     FROM metrics WHERE client_id=:cid AND waist_cm     IS NOT NULL ORDER BY date DESC LIMIT 6) s
UNION ALL
SELECT 'abdomenCm'  AS field, date::text AS date, abdomen_cm   AS value FROM (SELECT date, abdomen_cm   FROM metrics WHERE client_id=:cid AND abdomen_cm   IS NOT NULL ORDER BY date DESC LIMIT 6) s
ORDER BY field, date ASC
""")


class MetricsRepository(MetricsRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_client(self, client_id: uuid.UUID) -> List[Metric]:
        result = await self.session.execute(
            select(Metric)
            .where(Metric.client_id == client_id)
            .order_by(Metric.date.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, metric_id: uuid.UUID) -> Metric | None:
        result = await self.session.execute(
            select(Metric).where(Metric.id == metric_id)
        )
        return result.scalar_one_or_none()

    async def create(self, metric: Metric) -> Metric:
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric

    async def update(self, metric: Metric, data: dict) -> Metric:
        for key, value in data.items():
            if value is not None:
                setattr(metric, key, value)
        metric.updated_at = datetime.utcnow()
        self.session.add(metric)
        await self.session.commit()
        await self.session.refresh(metric)
        return metric

    async def delete(self, metric: Metric) -> None:
        await self.session.delete(metric)
        await self.session.commit()

    async def get_summary(self, client_id: uuid.UUID) -> Dict[str, Any]:
        params = {"cid": client_id}

        # --- deltas (1 row, 8 columns) ---
        delta_row = (await self.session.execute(_DELTA_SQL, params)).mappings().one()
        deltas = {
            "weightKg":   (delta_row["w_last"],  delta_row["w_prev"]),
            "bodyFatPct": (delta_row["f_last"],  delta_row["f_prev"]),
            "waistCm":    (delta_row["wc_last"], delta_row["wc_prev"]),
            "abdomenCm":  (delta_row["ab_last"], delta_row["ab_prev"]),
        }

        # --- series (multiple rows, already ordered ASC per field) ---
        series_rows = (await self.session.execute(_SERIES_SQL, params)).mappings().all()
        series: Dict[str, list] = {"weightKg": [], "bodyFatPct": [], "waistCm": [], "abdomenCm": []}
        for row in series_rows:
            series[row["field"]].append({"date": row["date"], "value": float(row["value"])})

        # --- history (all rows DESC) ---
        history = await self.list_by_client(client_id)

        return {"deltas": deltas, "series": series, "history": history}

    async def list_by_client_date_range(
        self, client_id: uuid.UUID, from_date: date, to_date: date,
    ) -> List[Metric]:
        result = await self.session.execute(
            select(Metric)
            .where(
                Metric.client_id == client_id,
                Metric.date >= from_date,
                Metric.date <= to_date,
            )
            .order_by(Metric.date.asc())
        )
        return list(result.scalars().all())
