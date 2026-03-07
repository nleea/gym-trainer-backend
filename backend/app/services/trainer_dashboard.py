import uuid
from datetime import date, timedelta
from typing import Any, Dict, List

from app.models.user import User
from app.repositories.implementations.postgres.trainer_dashboard_repo import TrainerDashboardRepository
from app.schemas.trainer_dashboard import (
    DashboardClientItem,
    LastCheckinSummary,
    RecentWorkoutItem,
    TrainerDashboardResponse,
    TrainerDashboardStats,
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
                for ex in (log.exercises or []):
                    if not isinstance(ex, dict):
                        continue
                    ex_count += 1
                    for s in (ex.get("sets") or []):
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
                for ex in (log.exercises or []):
                    if not isinstance(ex, dict):
                        continue
                    name = (ex.get("exerciseName") or "").strip()
                    for s in (ex.get("sets") or []):
                        w = float(s.get("weight") or 0)
                        if w > 0:
                            prev_maxes[name] = max(prev_maxes.get(name, 0.0), w)

            seen: set = set()
            for log in this_week:
                for ex in (log.exercises or []):
                    if not isinstance(ex, dict):
                        continue
                    name = (ex.get("exerciseName") or "").strip()
                    if not name or name in seen or name not in prev_maxes:
                        continue
                    max_w = max(
                        (float(s.get("weight") or 0) for s in (ex.get("sets") or [])),
                        default=0.0,
                    )
                    if max_w > prev_maxes[name]:
                        total += 1
                        seen.add(name)
        return total
