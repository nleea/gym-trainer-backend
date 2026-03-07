import json
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List

from app.models.user import User
from app.repositories.implementations.postgres.trainer_dashboard_repo import TrainerDashboardRepository
from app.schemas.trainer_dashboard import (
    AdherenceHistoryItem,
    AdherenceRankingItem,
    AttendanceDayItem,
    DashboardClientItem,
    GroupVolumeItem,
    LastCheckinSummary,
    PRThisWeekItem,
    RecentWorkoutItem,
    TrainerDashboardResponse,
    TrainerReportsResponse,
    TrainerReportsStats,
    TrainerDashboardStats,
    WeeklyProgressItem,
    WellbeingMoodDistribution,
    WellbeingSnapshot,
    WeightPoint,
)


class TrainerDashboardService:
    def __init__(self, repo: TrainerDashboardRepository) -> None:
        self.repo = repo

    async def get_dashboard(self, trainer: User) -> TrainerDashboardResponse:
        today = date.today()
        # Monday of the current week
        week_start = today - timedelta(days=today.weekday())

        # ── 1. Clients + user names ────────────────────────────────────
        clients_raw = await self.repo.get_clients_with_names(trainer.id)
        if not clients_raw:
            return TrainerDashboardResponse(
                stats=TrainerDashboardStats(
                    totalClients=0, activeThisWeek=0, inactiveClients=0, prsThisWeek=0
                ),
                clients=[],
            )

        client_ids = [c["client_id"] for c in clients_raw]

        # ── 2–7. Bulk data ──────────────────────────────────────────────
        logs_raw       = await self.repo.get_recent_logs(trainer.id, days=30)
        latest_metrics = await self.repo.get_latest_metrics(client_ids)
        prev_metrics   = await self.repo.get_prev_metrics(client_ids)
        weight_history = await self.repo.get_weight_history(client_ids)
        checkins_raw   = await self.repo.get_week_checkins(client_ids, week_start)
        metric_dates   = await self.repo.get_latest_metric_dates(client_ids)

        plan_ids  = [c["plan_id"]           for c in clients_raw if c["plan_id"]]
        nutr_ids  = [c["nutrition_plan_id"] for c in clients_raw if c["nutrition_plan_id"]]
        plan_names  = await self.repo.get_plan_names(plan_ids)
        nutr_names  = await self.repo.get_nutr_plan_names(nutr_ids)

        # ── Index raw data by client_id ─────────────────────────────────
        logs_by_client: Dict[str, List[Any]] = {cid: [] for cid in client_ids}
        for row in logs_raw:
            cid = str(row.client_id)
            if cid in logs_by_client:
                logs_by_client[cid].append(row)

        latest_weight:  Dict[str, float] = {
            r["client_id"]: r["weight_kg"] for r in latest_metrics if r["weight_kg"] is not None
        }
        prev_weight: Dict[str, float] = {
            r["client_id"]: r["weight_kg"] for r in prev_metrics if r["weight_kg"] is not None
        }
        weight_hist_by_client: Dict[str, List[Dict]] = {cid: [] for cid in client_ids}
        for r in weight_history:
            weight_hist_by_client[r["client_id"]].append(r)

        checkin_by_client = {r["client_id"]: r for r in checkins_raw}

        # ── PR detection (this week vs prior 3 weeks in 30-day window) ──
        pr_cutoff = week_start - timedelta(days=21)
        prs_total = self._count_prs(logs_by_client, week_start, pr_cutoff)

        # ── Build client items ──────────────────────────────────────────
        items: List[DashboardClientItem] = []
        active_this_week = 0
        inactive_count = 0

        for c in clients_raw:
            cid = c["client_id"]
            logs = logs_by_client.get(cid, [])

            # Status
            if c.get("status") == "inactive":
                inactive_count += 1

            # Last workout + streak
            sorted_logs = sorted(logs, key=lambda l: l.date, reverse=True)
            last_workout: date | None = sorted_logs[0].date if sorted_logs else None
            days_since = (today - last_workout).days if last_workout else None

            streak = self._compute_streak(sorted_logs, today)

            # This week workouts
            weekly = sum(1 for l in logs if l.date >= week_start)
            if weekly > 0:
                active_this_week += 1

            # 7-day workout dates (for activity bar)
            cutoff_7d = today - timedelta(days=6)
            workout_dates_7d = sorted(
                {str(l.date) for l in logs if l.date >= cutoff_7d}
            )

            # Recent 3 workouts for expanded panel
            recent_workouts = []
            for log in sorted_logs[:3]:
                vol = 0.0
                ex_count = 0
                for ex in self._iter_exercises(log.exercises):
                    ex_count += 1
                    for s in self._iter_sets(ex):
                        vol += float(s.get("weight") or 0) * float(s.get("reps") or 0)
                recent_workouts.append(RecentWorkoutItem(
                    date=str(log.date),
                    exerciseCount=ex_count,
                    volume=round(vol),
                    duration=log.duration,
                ))

            # Metrics + weight change
            wt = latest_weight.get(cid) or c.get("weight")
            pw = prev_weight.get(cid)
            weight_change = round(wt - pw, 1) if wt is not None and pw is not None else None

            weight_hist = [
                WeightPoint(date=r["date"], weightKg=r["weight_kg"])
                for r in weight_hist_by_client.get(cid, [])
            ]

            # Checkin
            checkin_row = checkin_by_client.get(cid)
            last_checkin = None
            if checkin_row:
                last_checkin = LastCheckinSummary(
                    mood=checkin_row["mood"],
                    energy=checkin_row["energy_level"],
                    stress=checkin_row["stress_level"],
                    weekStart=checkin_row["week_start"],
                )

            # Alerts
            alerts: List[str] = []
            if days_since is None or days_since >= 7:
                alerts.append("no_workout_7_days")
            elif days_since >= 3:
                alerts.append("no_workout_3_days")

            if not checkin_row:
                alerts.append("no_checkin")

            latest_metric_date = metric_dates.get(cid)
            if latest_metric_date is None or (today - latest_metric_date).days > 14:
                alerts.append("no_metrics_2_weeks")

            # Plan names
            plan_id = c.get("plan_id")
            nutr_id = c.get("nutrition_plan_id")

            items.append(DashboardClientItem(
                id=cid,
                name=c["user_name"],
                streak=streak,
                lastWorkout=str(last_workout) if last_workout else None,
                daysSinceLastWorkout=days_since,
                weeklyWorkouts=weekly,
                weightKg=wt,
                weightChange=weight_change,
                currentPlan=plan_names.get(plan_id) if plan_id else None,
                hasNutritionPlan=bool(nutr_id),
                lastCheckin=last_checkin,
                alerts=alerts,
                workoutDates7d=workout_dates_7d,
                recentWorkouts=recent_workouts,
                weightHistory=weight_hist,
            ))

        # Sort: most alerts first, then most recent activity
        items.sort(key=lambda x: (-len(x.alerts), x.daysSinceLastWorkout or 999))

        stats = TrainerDashboardStats(
            totalClients=len(clients_raw),
            activeThisWeek=active_this_week,
            inactiveClients=inactive_count,
            prsThisWeek=prs_total,
        )

        return TrainerDashboardResponse(stats=stats, clients=items)

    # ── Helpers ────────────────────────────────────────────────────────

    def _compute_streak(self, sorted_logs_desc: List[Any], today: date) -> int:
        workout_dates = {l.date for l in sorted_logs_desc}
        base = today if today in workout_dates else today - timedelta(days=1)
        streak = 0
        for i in range(len(workout_dates) + 1):
            d = base - timedelta(days=i)
            if d in workout_dates:
                streak += 1
            else:
                break
        return streak

    async def get_reports(
        self, trainer: User, trainer_id: str, period: str
    ) -> TrainerReportsResponse:
        if str(trainer.id) != str(trainer_id):
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        today = date.today()
        period_days = 7 if period == "week" else 30
        range_start = today - timedelta(days=period_days - 1)
        range_end = today
        week_start = today - timedelta(days=today.weekday())

        clients_raw = await self.repo.get_clients_with_names(trainer.id)
        if not clients_raw:
            return TrainerReportsResponse(
                stats=TrainerReportsStats(
                    activeClients=0, avgAttendance=0, totalWorkouts=0, totalMeals=0, prsThisWeek=0
                ),
                attendance=[],
                adherenceRanking=[],
                weeklyProgress=[],
                groupVolume=[],
                wellbeingSnapshot=WellbeingSnapshot(
                    avgStress=0.0,
                    avgEnergy=0.0,
                    avgSleep=0.0,
                    moodDistribution=WellbeingMoodDistribution(
                        great=0, good=0, neutral=0, bad=0, terrible=0
                    ),
                    clientsWithCheckin=0,
                    clientsWithoutCheckin=0,
                ),
                prsThisWeek=[],
                adherenceHistory=[],
            )

        client_ids = [c["client_id"] for c in clients_raw]
        name_by_client = {c["client_id"]: c["user_name"] for c in clients_raw}
        plan_ids = [c["plan_id"] for c in clients_raw if c.get("plan_id")]

        attendance_rows = await self.repo.get_attendance_rows(trainer.id, range_start, range_end)
        training_rows = await self.repo.get_training_logs_rows(trainer.id, range_start, range_end)
        meal_rows = await self.repo.get_meal_logs_rows(trainer.id, range_start, range_end)
        checkins_rows = await self.repo.get_weekly_checkins_rows(trainer.id, week_start, today)
        plans_weeks = await self.repo.get_training_plan_weeks(plan_ids)

        week_logs = await self.repo.get_training_logs_rows(trainer.id, week_start, today)
        prev_logs = await self.repo.get_training_logs_rows_before(trainer.id, week_start, 28)
        week_prs = self._build_prs_list(week_logs, prev_logs, name_by_client)

        # Attendance chart
        attendance_by_day: Dict[str, Dict[str, int]] = {}
        d = range_start
        while d <= range_end:
            key = d.isoformat()
            attendance_by_day[key] = {"attended": 0, "missed": 0}
            d += timedelta(days=1)
        for row in attendance_rows:
            bucket = attendance_by_day.get(row["date"])
            if not bucket:
                continue
            if row.get("attended"):
                bucket["attended"] += 1
            else:
                bucket["missed"] += 1
        attendance = [
            AttendanceDayItem(
                day=self._weekday_short(iso),
                attended=vals["attended"],
                missed=vals["missed"],
            )
            for iso, vals in sorted(attendance_by_day.items())
        ]

        # Planned workouts and per-client aggregations
        planned_by_client: Dict[str, int] = {}
        for c in clients_raw:
            pid = c.get("plan_id")
            planned_by_client[c["client_id"]] = self._planned_workouts_from_weeks(
                plans_weeks.get(pid), period
            )

        workouts_by_client: Dict[str, int] = defaultdict(int)
        meals_by_client: Dict[str, int] = defaultdict(int)
        volume_by_client: Dict[str, float] = defaultdict(float)
        workout_dates_by_client: Dict[str, set] = defaultdict(set)
        for row in training_rows:
            cid = row["client_id"]
            workouts_by_client[cid] += 1
            workout_dates_by_client[cid].add(row["date"])
            volume_by_client[cid] += self._volume_from_exercises(row.get("exercises"))
        for row in meal_rows:
            meals_by_client[row["client_id"]] += 1

        prs_by_client: Dict[str, int] = defaultdict(int)
        for pr in week_prs:
            cid = self._client_id_by_name(pr.clientName, name_by_client)
            if cid:
                prs_by_client[cid] += 1

        adherence_ranking: List[AdherenceRankingItem] = []
        weekly_progress: List[WeeklyProgressItem] = []
        for cid in client_ids:
            planned = max(planned_by_client.get(cid, 0), 1)
            workouts = workouts_by_client.get(cid, 0)
            meals = meals_by_client.get(cid, 0)
            adherence = round((workouts / planned) * 100)
            adherence = max(0, min(100, adherence))
            streak = self._streak_from_dates(workout_dates_by_client.get(cid, set()), today)

            adherence_ranking.append(
                AdherenceRankingItem(
                    clientId=cid,
                    clientName=name_by_client.get(cid, "Cliente"),
                    avatar=None,
                    workouts=workouts,
                    plannedWorkouts=planned,
                    meals=meals,
                    adherencePct=adherence,
                )
            )
            weekly_progress.append(
                WeeklyProgressItem(
                    clientId=cid,
                    clientName=name_by_client.get(cid, "Cliente"),
                    avatar=None,
                    completedWorkouts=workouts,
                    plannedWorkouts=planned,
                    volumeKg=round(volume_by_client.get(cid, 0.0), 2),
                    prs=prs_by_client.get(cid, 0),
                    streak=streak,
                )
            )

        adherence_ranking.sort(key=lambda x: x.adherencePct, reverse=True)
        weekly_progress.sort(
            key=lambda x: (
                x.completedWorkouts / max(1, x.plannedWorkouts),
                x.volumeKg,
            ),
            reverse=True,
        )

        # Group volume last 8 weeks
        weeks_data = await self.repo.get_training_logs_rows(trainer.id, today - timedelta(days=55), today)
        group_volume_map: Dict[str, float] = defaultdict(float)
        for row in weeks_data:
            d_obj = date.fromisoformat(row["date"])
            monday = d_obj - timedelta(days=d_obj.weekday())
            group_volume_map[monday.isoformat()] += self._volume_from_exercises(row.get("exercises"))
        group_volume = [
            GroupVolumeItem(week=week, volume=round(group_volume_map[week], 2))
            for week in sorted(group_volume_map.keys())[-8:]
        ]

        # Wellbeing
        moods = {"great": 0, "good": 0, "neutral": 0, "bad": 0, "terrible": 0}
        stress_values = []
        energy_values = []
        sleep_values = []
        clients_with_checkin = set()
        for c in checkins_rows:
            cid = c["client_id"]
            clients_with_checkin.add(cid)
            mood_key = self._map_mood(c.get("mood"))
            moods[mood_key] += 1
            if c.get("stress_level") is not None:
                stress_values.append(float(c["stress_level"]))
            if c.get("energy_level") is not None:
                energy_values.append(float(c["energy_level"]))
            if c.get("sleep_hours") is not None:
                sleep_values.append(float(c["sleep_hours"]))

        wellbeing = WellbeingSnapshot(
            avgStress=round(sum(stress_values) / len(stress_values), 1) if stress_values else 0.0,
            avgEnergy=round(sum(energy_values) / len(energy_values), 1) if energy_values else 0.0,
            avgSleep=round(sum(sleep_values) / len(sleep_values), 1) if sleep_values else 0.0,
            moodDistribution=WellbeingMoodDistribution(**moods),
            clientsWithCheckin=len(clients_with_checkin),
            clientsWithoutCheckin=max(0, len(client_ids) - len(clients_with_checkin)),
        )

        # Adherence history last 6 months
        adherence_history = await self._build_adherence_history(trainer.id, client_ids, planned_by_client)

        total_att = len(attendance_rows)
        attended = sum(1 for a in attendance_rows if a.get("attended"))
        stats = TrainerReportsStats(
            activeClients=sum(1 for c in clients_raw if c.get("status") != "inactive"),
            avgAttendance=round((attended / total_att) * 100) if total_att else 0,
            totalWorkouts=len(training_rows),
            totalMeals=len(meal_rows),
            prsThisWeek=len(week_prs),
        )

        return TrainerReportsResponse(
            stats=stats,
            attendance=attendance,
            adherenceRanking=adherence_ranking,
            weeklyProgress=weekly_progress,
            groupVolume=group_volume,
            wellbeingSnapshot=wellbeing,
            prsThisWeek=week_prs,
            adherenceHistory=adherence_history,
        )

    def _count_prs(
        self,
        logs_by_client: Dict[str, List[Any]],
        week_start: date,
        prev_start: date,
    ) -> int:
        total = 0
        for logs in logs_by_client.values():
            this_week = [l for l in logs if l.date >= week_start]
            prev_logs  = [l for l in logs if prev_start <= l.date < week_start]

            prev_maxes: Dict[str, float] = {}
            for log in prev_logs:
                for ex in self._iter_exercises(log.exercises):
                    name = (ex.get("exerciseName") or "").strip()
                    for s in self._iter_sets(ex):
                        w = float(s.get("weight") or 0)
                        if w > 0:
                            prev_maxes[name] = max(prev_maxes.get(name, 0.0), w)

            seen: set = set()
            for log in this_week:
                for ex in self._iter_exercises(log.exercises):
                    name = (ex.get("exerciseName") or "").strip()
                    if not name or name in seen or name not in prev_maxes:
                        continue
                    max_w = max(
                        (float(s.get("weight") or 0) for s in self._iter_sets(ex)),
                        default=0.0,
                    )
                    if max_w > prev_maxes[name]:
                        total += 1
                        seen.add(name)
        return total

    def _iter_exercises(self, exercises: Any) -> List[Dict[str, Any]]:
        raw = exercises
        if raw is None:
            return []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                return []
        if not isinstance(raw, list):
            return []
        return [ex for ex in raw if isinstance(ex, dict)]

    def _iter_sets(self, exercise: Dict[str, Any]) -> List[Dict[str, Any]]:
        sets = exercise.get("sets") or []
        if isinstance(sets, str):
            try:
                sets = json.loads(sets)
            except Exception:
                return []
        if not isinstance(sets, list):
            return []
        return [s for s in sets if isinstance(s, dict)]

    def _volume_from_exercises(self, exercises: Any) -> float:
        total = 0.0
        for ex in self._iter_exercises(exercises):
            for s in self._iter_sets(ex):
                total += float(s.get("weight") or 0) * float(s.get("reps") or 0)
        return total

    def _weekday_short(self, iso_date: str) -> str:
        d = date.fromisoformat(iso_date)
        labels = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
        return labels[d.weekday()]

    def _planned_workouts_from_weeks(self, weeks_raw: Any, period: str) -> int:
        weeks = weeks_raw if isinstance(weeks_raw, list) else []
        if not weeks:
            return 4 if period == "week" else 16
        days_per_week = max((len((w or {}).get("days") or []) for w in weeks), default=4)
        return days_per_week if period == "week" else days_per_week * 4

    def _streak_from_dates(self, iso_dates: set, today: date) -> int:
        parsed = {date.fromisoformat(d) for d in iso_dates if d}
        if not parsed:
            return 0
        base = today if today in parsed else (today - timedelta(days=1))
        streak = 0
        while base in parsed:
            streak += 1
            base -= timedelta(days=1)
        return streak

    def _build_prs_list(
        self, week_logs: List[Dict[str, Any]], prev_logs: List[Dict[str, Any]], name_by_client: Dict[str, str]
    ) -> List[PRThisWeekItem]:
        prev_max: Dict[tuple[str, str], float] = {}
        for row in prev_logs:
            cid = row["client_id"]
            for ex in self._iter_exercises(row.get("exercises")):
                ex_name = str(ex.get("exerciseName") or "").strip()
                if not ex_name:
                    continue
                key = (cid, ex_name)
                prev_max[key] = max(
                    prev_max.get(key, 0.0),
                    max((float(s.get("weight") or 0) for s in self._iter_sets(ex)), default=0.0),
                )

        prs: List[PRThisWeekItem] = []
        for row in sorted(week_logs, key=lambda r: r["date"], reverse=True):
            cid = row["client_id"]
            for ex in self._iter_exercises(row.get("exercises")):
                ex_name = str(ex.get("exerciseName") or "").strip()
                if not ex_name:
                    continue
                key = (cid, ex_name)
                new_w = max((float(s.get("weight") or 0) for s in self._iter_sets(ex)), default=0.0)
                prev_w = prev_max.get(key, 0.0)
                if new_w > 0 and new_w > prev_w:
                    prs.append(
                        PRThisWeekItem(
                            clientName=name_by_client.get(cid, "Cliente"),
                            exerciseName=ex_name,
                            newWeight=new_w,
                            previousBest=prev_w,
                            date=row["date"],
                        )
                    )
                    prev_max[key] = new_w
        return prs

    async def _build_adherence_history(
        self, trainer_id: Any, client_ids: List[str], planned_by_client: Dict[str, int]
    ) -> List[AdherenceHistoryItem]:
        today = date.today()
        first_month = date(today.year, today.month, 1)
        months = []
        cursor = first_month
        for _ in range(6):
            months.append(cursor)
            if cursor.month == 1:
                cursor = date(cursor.year - 1, 12, 1)
            else:
                cursor = date(cursor.year, cursor.month - 1, 1)
        months = sorted(months)

        history: List[AdherenceHistoryItem] = []
        for month_start in months:
            if month_start.month == 12:
                month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
            logs = await self.repo.get_training_logs_rows(trainer_id, month_start, month_end)
            by_client: Dict[str, int] = defaultdict(int)
            for row in logs:
                by_client[row["client_id"]] += 1

            values = []
            for cid in client_ids:
                planned = max(1, planned_by_client.get(cid, 4) * 4)
                adherence = round((by_client.get(cid, 0) / planned) * 100)
                values.append(max(0, min(100, adherence)))
            avg = round(sum(values) / len(values)) if values else 0
            history.append(AdherenceHistoryItem(month=month_start.strftime("%Y-%m"), adherencePct=avg))
        return history

    def _map_mood(self, mood: Any) -> str:
        value = str(mood or "").strip().lower()
        mapping = {
            "excellent": "great",
            "very_good": "good",
            "good": "good",
            "regular": "neutral",
            "neutral": "neutral",
            "bad": "bad",
            "terrible": "terrible",
        }
        return mapping.get(value, "neutral")

    def _client_id_by_name(self, client_name: str, name_by_client: Dict[str, str]) -> str | None:
        for cid, name in name_by_client.items():
            if name == client_name:
                return cid
        return None
