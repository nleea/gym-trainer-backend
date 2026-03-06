import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.metric import Metric
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.metricsInterface import MetricsRepositoryInterface
from app.schemas.metric import MetricCreate, MetricUpdate, MetricResponse, MetricsSummaryResponse


class MetricsService:
    def __init__(
        self,
        metrics_repo: MetricsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.metrics_repo = metrics_repo
        self.clients_repo = clients_repo

    async def _assert_can_access_client(self, client_id: uuid.UUID, current_user: User) -> None:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        if current_user.role == "trainer":
            if client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self.clients_repo.get_by_user_id(current_user.id)
            if not own_client or own_client.id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_metrics(self, client_id: uuid.UUID, current_user: User) -> List[Metric]:
        await self._assert_can_access_client(client_id, current_user)
        return await self.metrics_repo.list_by_client(client_id)

    async def create_metric(self, data: MetricCreate, current_user: User) -> Metric:
        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
            )
        metric = Metric(
            client_id=client.id,
            **data.model_dump(exclude_none=False),
        )
        return await self.metrics_repo.create(metric)

    async def update_metric(
        self, metric_id: uuid.UUID, data: MetricUpdate, current_user: User
    ) -> Metric:
        metric = await self.metrics_repo.get_by_id(metric_id)
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client or metric.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.metrics_repo.update(metric, data.model_dump(exclude_none=True))

    async def delete_metric(self, metric_id: uuid.UUID, current_user: User) -> None:
        metric = await self.metrics_repo.get_by_id(metric_id)
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")

        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client or metric.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await self.metrics_repo.delete(metric)

    async def get_metrics_summary(
        self, client_id: uuid.UUID, current_user: User
    ) -> MetricsSummaryResponse:
        await self._assert_can_access_client(client_id, current_user)
        raw = await self.metrics_repo.get_summary(client_id)

        deltas = {}
        for key, (last_val, prev_val) in raw["deltas"].items():
            change = round(last_val - prev_val, 2) if last_val is not None and prev_val is not None else None
            deltas[key] = {"lastValue": last_val, "change": change}

        history = [MetricResponse.model_validate(m) for m in raw["history"]]

        return MetricsSummaryResponse(
            deltas=deltas,
            series=raw["series"],
            history=history,
        )
