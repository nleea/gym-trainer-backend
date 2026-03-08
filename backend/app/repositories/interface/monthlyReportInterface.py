import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.monthly_report import MonthlyReport


class MonthlyReportRepositoryInterface(ABC):

    @abstractmethod
    async def list_by_client(self, client_id: uuid.UUID) -> List[MonthlyReport]: ...

    @abstractmethod
    async def get_by_client_and_month(self, client_id: uuid.UUID, month: str) -> Optional[MonthlyReport]: ...

    @abstractmethod
    async def create(self, report: MonthlyReport) -> MonthlyReport: ...
