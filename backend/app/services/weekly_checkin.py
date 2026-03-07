import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status

from app.models.weekly_checkin import WeeklyCheckin
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.weeklyCheckinInterface import WeeklyCheckinRepositoryInterface
from app.schemas.weekly_checkin import WeeklyCheckinCreate, WeeklyCheckinUpdate


class WeeklyCheckinService:
    def __init__(
        self,
        checkin_repo: WeeklyCheckinRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.checkin_repo = checkin_repo
        self.clients_repo = clients_repo

    async def _get_client_for_user(self, user: User):
        client = await self.clients_repo.get_by_user_id(user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )
        return client

    def _current_week_start(self) -> date:
        today = date.today()
        return today - timedelta(days=today.weekday())  # Monday

    async def upsert_checkin(self, data: WeeklyCheckinCreate, current_user: User) -> WeeklyCheckin:
        client = await self._get_client_for_user(current_user)
        existing = await self.checkin_repo.get_by_client_and_week(client.id, data.week_start)
        if existing:
            update_data = data.model_dump(exclude={"week_start"}, exclude_none=True)
            return await self.checkin_repo.update(existing, update_data)

        checkin = WeeklyCheckin(
            client_id=client.id,
            trainer_id=client.trainer_id,
            week_start=data.week_start,
            sleep_hours=data.sleep_hours,
            sleep_quality=data.sleep_quality,
            stress_level=data.stress_level,
            energy_level=data.energy_level,
            muscle_soreness=data.muscle_soreness,
            mood=data.mood,
            notes=data.notes,
        )
        return await self.checkin_repo.create(checkin)

    async def get_current_checkin(
        self,
        client_id: Optional[uuid.UUID],
        current_user: User,
    ) -> WeeklyCheckin | None:
        if current_user.role == "client":
            client = await self._get_client_for_user(current_user)
            target_client_id = client.id
        else:
            if not client_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="client_id required")
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            target_client_id = client_id

        week_start = self._current_week_start()
        return await self.checkin_repo.get_by_client_and_week(target_client_id, week_start)

    async def list_checkins(
        self,
        client_id: Optional[uuid.UUID],
        current_user: User,
    ) -> List[WeeklyCheckin]:
        if current_user.role == "client":
            client = await self._get_client_for_user(current_user)
            target_client_id = client.id
        else:
            if not client_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="client_id required")
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            target_client_id = client_id

        return await self.checkin_repo.list_by_client(target_client_id)

    async def update_checkin(
        self,
        checkin_id: uuid.UUID,
        data: WeeklyCheckinUpdate,
        current_user: User,
    ) -> WeeklyCheckin:
        checkin = await self.checkin_repo.get_by_id(checkin_id)
        if not checkin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")

        client = await self._get_client_for_user(current_user)
        if checkin.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.checkin_repo.update(checkin, data.model_dump(exclude_none=True))
