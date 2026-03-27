import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.schemas.streak import StreakResponse


class StreakService:
    def __init__(
        self,
        training_logs_repo: TrainingLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
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

    async def get_streak(
        self, client_id: uuid.UUID, current_user: User,
    ) -> StreakResponse:
        await self._assert_access(client_id, current_user)

        dates = await self.training_logs_repo.get_workout_dates(client_id)
        if not dates:
            return StreakResponse(current=0, best=0, last_activity="")

        # dates come sorted DESC from repo
        last_activity = dates[0]
        today = date.today()

        # Current streak: count consecutive days ending at today or yesterday
        current = 0
        expected = today
        # If the most recent workout is not today or yesterday, streak is 0
        if last_activity < today - timedelta(days=1):
            current = 0
        else:
            if last_activity == today:
                expected = today
            else:
                expected = today - timedelta(days=1)
            for d in dates:
                if d == expected:
                    current += 1
                    expected -= timedelta(days=1)
                elif d < expected:
                    break

        # Best streak: scan all dates (sorted DESC)
        best = 1
        run = 1
        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1] - timedelta(days=1):
                run += 1
                best = max(best, run)
            else:
                run = 1

        return StreakResponse(
            current=current,
            best=max(best, current),
            last_activity=str(last_activity),
        )
