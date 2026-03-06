import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.attendance import Attendance
from app.models.user import User
from app.repositories.interface.attendanceInterface import AttendanceRepositoryInterface
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class AttendanceService:
    def __init__(
        self,
        attendance_repo: AttendanceRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.attendance_repo = attendance_repo
        self.clients_repo = clients_repo

    def _assert_trainer_owns_client_id(self, client_trainer_id: uuid.UUID, trainer: User) -> None:
        if client_trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_attendance_by_trainer(self, trainer: User) -> List[Attendance]:
        return await self.attendance_repo.list_by_trainer(trainer.id)

    async def list_attendance(self, client_id: uuid.UUID, trainer: User) -> List[Attendance]:
        client = await self.clients_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        self._assert_trainer_owns_client_id(client.trainer_id, trainer)
        return await self.attendance_repo.list_by_client(client_id)

    async def create_attendance(self, data: AttendanceCreate, trainer: User) -> Attendance:
        client = await self.clients_repo.get_by_id(data.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        self._assert_trainer_owns_client_id(client.trainer_id, trainer)

        record = Attendance(
            client_id=data.client_id,
            trainer_id=trainer.id,
            date=data.date,
            attended=data.attended,
            notes=data.notes,
        )
        return await self.attendance_repo.create(record)

    async def update_attendance(
        self, attendance_id: uuid.UUID, data: AttendanceUpdate, trainer: User
    ) -> Attendance:
        record = await self.attendance_repo.get_by_id(attendance_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found"
            )
        if record.trainer_id != trainer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await self.attendance_repo.update(record, data.model_dump(exclude_none=True))
