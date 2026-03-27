import uuid
from datetime import date
from typing import List

from fastapi import HTTPException, status

from app.models.daily_wellness import DailyWellness
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.dailyWellnessInterface import DailyWellnessRepositoryInterface
from app.schemas.daily_wellness import DailyWellnessCreate


class DailyWellnessService:
    def __init__(
        self,
        wellness_repo: DailyWellnessRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.wellness_repo = wellness_repo
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

    async def create_wellness(
        self, data: DailyWellnessCreate, current_user: User,
    ) -> DailyWellness:
        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )

        existing = await self.wellness_repo.get_by_client_and_date(client.id, data.date)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Wellness entry already exists for this date",
            )

        record = DailyWellness(
            client_id=client.id,
            date=data.date,
            energy=data.energy,
            sleep_quality=data.sleep_quality,
            muscle_fatigue=data.muscle_fatigue,
            notes=data.notes,
        )
        return await self.wellness_repo.create(record)

    async def list_wellness(
        self,
        client_id: uuid.UUID,
        from_date: date,
        to_date: date,
        current_user: User,
    ) -> List[DailyWellness]:
        await self._assert_access(client_id, current_user)
        return await self.wellness_repo.list_by_client_date_range(
            client_id, from_date, to_date
        )
