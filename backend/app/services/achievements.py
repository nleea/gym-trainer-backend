import uuid
from datetime import datetime
from typing import List

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.interface.achievementsInterface import AchievementsRepositoryInterface
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.schemas.achievement import (
    AchievementItem,
    AchievementSummaryLatest,
    AchievementSummaryResponse,
)


class AchievementsService:
    def __init__(
        self,
        achievements_repo: AchievementsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.achievements_repo = achievements_repo
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

    async def list_achievements(
        self, client_id: uuid.UUID, current_user: User,
    ) -> List[AchievementItem]:
        await self._assert_access(client_id, current_user)

        all_achievements = await self.achievements_repo.list_all()
        client_map = await self.achievements_repo.get_client_achievements(client_id)

        items: List[AchievementItem] = []
        for ach in all_achievements:
            ca = client_map.get(ach.id)
            items.append(
                AchievementItem(
                    id=ach.id,
                    slug=ach.slug,
                    title=ach.title,
                    description=ach.description,
                    icon=ach.icon,
                    category=ach.category,
                    unlocked=ca.unlocked if ca else False,
                    unlocked_at=str(ca.unlocked_at.date()) if ca and ca.unlocked_at else None,
                    progress=ca.progress if ca else 0,
                    target=ach.target,
                )
            )
        return items

    async def get_summary(
        self, client_id: uuid.UUID, current_user: User,
    ) -> AchievementSummaryResponse:
        await self._assert_access(client_id, current_user)

        all_achievements = await self.achievements_repo.list_all()
        client_map = await self.achievements_repo.get_client_achievements(client_id)

        total = len(all_achievements)
        unlocked_list = [
            ca for ca in client_map.values() if ca.unlocked
        ]
        unlocked_count = len(unlocked_list)

        # Latest unlocked achievements (up to 3, most recent first)
        unlocked_list.sort(key=lambda ca: ca.unlocked_at or datetime.min, reverse=True)
        ach_by_id = {a.id: a for a in all_achievements}

        latest: List[AchievementSummaryLatest] = []
        for ca in unlocked_list[:3]:
            ach = ach_by_id.get(ca.achievement_id)
            if ach and ca.unlocked_at:
                latest.append(
                    AchievementSummaryLatest(
                        slug=ach.slug,
                        title=ach.title,
                        icon=ach.icon,
                        unlocked_at=str(ca.unlocked_at.date()),
                    )
                )

        return AchievementSummaryResponse(
            total=total, unlocked=unlocked_count, latest=latest,
        )

    async def check_achievement(
        self, client_id: uuid.UUID, achievement_id: uuid.UUID, progress: int,
    ) -> None:
        """Update progress and unlock if target is reached. Called internally post-workout."""
        all_achievements = await self.achievements_repo.list_all()
        ach_by_id = {a.id: a for a in all_achievements}
        ach = ach_by_id.get(achievement_id)
        if not ach:
            return

        record = await self.achievements_repo.get_or_create_client_achievement(
            client_id, achievement_id,
        )
        if record.unlocked:
            return

        update_data: dict = {"progress": progress}
        if progress >= ach.target:
            update_data["unlocked"] = True
            update_data["unlocked_at"] = datetime.utcnow()

        await self.achievements_repo.update_client_achievement(record, update_data)

    async def evaluate_post_workout(
        self,
        client_id: uuid.UUID,
        total_workouts: int,
        current_streak: int,
        had_pr: bool,
    ) -> None:
        """Evaluate all achievement rules after a workout is logged.

        Called from TrainingLogsService.create_or_upsert_log with pre-computed stats.
        """
        all_achievements = await self.achievements_repo.list_all()

        # Map slug → achievement for rule matching
        slug_map = {a.slug: a for a in all_achievements}

        # Category: workouts (based on total workout count)
        for slug in ("first-workout", "ten-workouts", "fifty-workouts", "hundred-workouts"):
            ach = slug_map.get(slug)
            if ach:
                await self.check_achievement(client_id, ach.id, total_workouts)

        # Category: streaks (based on current streak)
        for slug in ("week-streak", "month-streak"):
            ach = slug_map.get(slug)
            if ach:
                await self.check_achievement(client_id, ach.id, current_streak)

        # Category: strength (based on PR detection)
        if had_pr:
            ach = slug_map.get("first-pr")
            if ach:
                await self.check_achievement(client_id, ach.id, 1)
