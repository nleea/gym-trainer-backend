import uuid
from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status

from app.models.training_log import TrainingLog
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.schemas.training_log import TrainingLogCreate, TrainingLogUpdate, PRItem


class TrainingLogsService:
    def __init__(
        self,
        logs_repo: TrainingLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.logs_repo = logs_repo
        self.clients_repo = clients_repo

    async def _get_client_for_user(self, user: User):
        client = await self.clients_repo.get_by_user_id(user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )
        return client

    async def list_logs(
        self,
        current_user: User,
        client_id: Optional[uuid.UUID] = None,
        week_start: Optional[date] = None,
    ) -> List[TrainingLog]:
        if current_user.role == "client":
            client = await self._get_client_for_user(current_user)
            client_id = client.id
        return await self.logs_repo.list_by_filters(client_id=client_id, week_start=week_start)

    async def create_or_upsert_log(
        self, data: TrainingLogCreate, current_user: User
    ) -> dict:
        client = await self._get_client_for_user(current_user)

        existing = await self.logs_repo.get_by_client_and_date(client.id, data.date)
        if existing:
            saved_log = await self.logs_repo.update(
                existing, data.model_dump(exclude={"date"}, exclude_none=True)
            )
        else:
            log = TrainingLog(
                client_id=client.id,
                trainer_id=client.trainer_id,
                date=data.date,
                exercises=[ex.model_dump() for ex in (data.exercises or [])],
                duration=data.duration,
                notes=data.notes,
                effort=data.effort,
            )
            saved_log = await self.logs_repo.create(log)

        # PR detection: compare new max weights against historical best before today
        hist = await self.logs_repo.get_max_weights_before_date(client.id, data.date)
        prs: list[PRItem] = []
        for ex in (data.exercises or []):
            sets = ex.sets or []
            new_max = max((s.weight for s in sets), default=0.0)
            prev_best = hist.get(str(ex.exerciseId), 0.0)
            if new_max > 0 and new_max > prev_best:
                prs.append(PRItem(
                    exerciseName=ex.exerciseName,
                    newWeight=new_max,
                    previousBest=prev_best,
                ))

        return {"log": saved_log, "prs": prs}

    async def update_log(
        self, log_id: uuid.UUID, data: TrainingLogUpdate, current_user: User
    ) -> TrainingLog:
        log = await self.logs_repo.get_by_id(log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

        client = await self._get_client_for_user(current_user)
        if log.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.logs_repo.update(log, data.model_dump(exclude_none=True))

    async def get_week_logs(
        self, client_id: uuid.UUID, week_start: date, current_user: User
    ) -> List[TrainingLog]:
        if current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self._get_client_for_user(current_user)
            if own_client.id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.logs_repo.list_by_client_week(client_id, week_start)

    async def get_last_performance(
        self, client_id: uuid.UUID, exercise_ids: List[str], current_user: User
    ) -> list:
        if current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self._get_client_for_user(current_user)
            if own_client.id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.logs_repo.get_last_performance(client_id, exercise_ids)
