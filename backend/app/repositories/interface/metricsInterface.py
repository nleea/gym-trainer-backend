from abc import ABC, abstractmethod
from uuid import UUID
from typing import Any, Dict, List

from app.models.metric import Metric


class MetricsRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_client(self, client_id: UUID) -> List[Metric]:
        pass

    @abstractmethod
    async def get_by_id(self, metric_id: UUID) -> Metric | None:
        pass

    @abstractmethod
    async def create(self, metric: Metric) -> Metric:
        pass

    @abstractmethod
    async def update(self, metric: Metric, data: dict) -> Metric:
        pass

    @abstractmethod
    async def delete(self, metric: Metric) -> None:
        pass

    @abstractmethod
    async def get_summary(self, client_id: UUID) -> Dict[str, Any]:
        """Returns dict with keys: deltas, series, history."""
        pass
