import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.dailyWellnessInterface import DailyWellnessRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.schemas.wellness_insights import (
    TodayWellnessEntry,
    WellnessCorrelationPoint,
    WellnessCorrelationResponse,
    WellnessSummaryResponse,
)


class WellnessInsightsService:
    def __init__(
        self,
        wellness_repo: DailyWellnessRepositoryInterface,
        training_logs_repo: TrainingLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.wellness_repo = wellness_repo
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

    @staticmethod
    def _calc_readiness(energy: int, fatigue: int, sleep_quality: int) -> float:
        """readiness = (energy * 0.4 + (6 - fatigue) * 0.4 + sleep_quality * 0.2), normalized 1-10."""
        raw = energy * 0.4 + (6 - fatigue) * 0.4 + sleep_quality * 0.2
        # raw range: min = 1*0.4 + (6-5)*0.4 + 1*0.2 = 0.4+0.4+0.2 = 1.0
        # raw range: max = 5*0.4 + (6-1)*0.4 + 5*0.2 = 2.0+2.0+1.0 = 5.0
        # Normalize 1.0-5.0 → 1-10
        normalized = 1 + (raw - 1.0) * (9.0 / 4.0)
        return round(max(1.0, min(10.0, normalized)), 1)

    @staticmethod
    def _detect_overload(entries) -> bool:
        """True if muscle_fatigue >= 4 for 3+ consecutive days (sorted by date ASC)."""
        consecutive = 0
        for entry in entries:
            if entry.muscle_fatigue >= 4:
                consecutive += 1
                if consecutive >= 3:
                    return True
            else:
                consecutive = 0
        return False

    async def get_wellness_summary(
        self, client_id: uuid.UUID, current_user: User,
    ) -> WellnessSummaryResponse:
        await self._assert_access(client_id, current_user)

        today = date.today()
        from_date = today - timedelta(days=13)  # extra days for overload detection
        entries = await self.wellness_repo.list_by_client_date_range(
            client_id, from_date, today
        )

        if not entries:
            return WellnessSummaryResponse(
                overload_alert=False,
                avg_fatigue_7d=0.0,
                avg_energy_7d=0.0,
                readiness_score=None,
                today_entry=None,
            )

        # Last 7 days for averages
        seven_days_ago = today - timedelta(days=6)
        recent = [e for e in entries if e.date >= seven_days_ago]

        avg_fatigue = round(
            sum(e.muscle_fatigue for e in recent) / len(recent), 1
        ) if recent else 0.0
        avg_energy = round(
            sum(e.energy for e in recent) / len(recent), 1
        ) if recent else 0.0

        # Overload detection on all entries (need consecutive days)
        overload = self._detect_overload(entries)

        # Today's entry
        today_entry: Optional[TodayWellnessEntry] = None
        readiness: Optional[float] = None
        for e in entries:
            if e.date == today:
                today_entry = TodayWellnessEntry(
                    energy=e.energy,
                    sleep_quality=e.sleep_quality,
                    muscle_fatigue=e.muscle_fatigue,
                )
                readiness = self._calc_readiness(
                    e.energy, e.muscle_fatigue, e.sleep_quality
                )
                break

        return WellnessSummaryResponse(
            overload_alert=overload,
            avg_fatigue_7d=avg_fatigue,
            avg_energy_7d=avg_energy,
            readiness_score=readiness,
            today_entry=today_entry,
        )

    async def get_wellness_correlation(
        self,
        client_id: uuid.UUID,
        from_date: date,
        to_date: date,
        current_user: User,
    ) -> WellnessCorrelationResponse:
        await self._assert_access(client_id, current_user)

        # Get wellness entries and volume in the range
        entries = await self.wellness_repo.list_by_client_date_range(
            client_id, from_date, to_date
        )
        volume_rows = await self.training_logs_repo.get_volume_by_date_range(
            client_id, from_date, to_date
        )

        # Group wellness by week (Monday start)
        fatigue_by_week: dict[str, List[int]] = defaultdict(list)
        for e in entries:
            monday = e.date - timedelta(days=e.date.weekday())
            week_key = str(monday)
            fatigue_by_week[week_key].append(e.muscle_fatigue)

        # Volume by week
        volume_by_week = {r["week"]: r["volume"] for r in volume_rows}

        # Merge: all weeks that appear in either dataset
        all_weeks = sorted(set(fatigue_by_week.keys()) | set(volume_by_week.keys()))

        points: List[WellnessCorrelationPoint] = []
        for week in all_weeks:
            fatigue_vals = fatigue_by_week.get(week, [])
            avg_f = round(sum(fatigue_vals) / len(fatigue_vals), 1) if fatigue_vals else 0.0
            vol = volume_by_week.get(week, 0.0)
            points.append(
                WellnessCorrelationPoint(week=week, avg_fatigue=avg_f, volume=vol)
            )

        return WellnessCorrelationResponse(points=points)
