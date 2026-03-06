from abc import ABC, abstractmethod
from uuid import UUID
from app.models.attendance import Attendance

class AttendanceRepositoryInterface(ABC):
    @abstractmethod
    async def list_by_client(self, client_id: UUID) -> list[Attendance]:
        pass
    
    @abstractmethod
    async def list_by_trainer(self, trainer_id: UUID) -> list[Attendance]:
        pass

    @abstractmethod
    async def get_by_id(self, attendance_id: UUID) -> Attendance | None:
        pass

    @abstractmethod
    async def create(self, record) -> Attendance:
        pass

    @abstractmethod
    async def update(self, record, data: dict) -> Attendance:
        pass