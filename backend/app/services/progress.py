import uuid
from typing import List

from fastapi import HTTPException, status

from app.models.progress_entry import ProgressEntry
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.progressInterface import ProgressRepositoryInterface
from app.schemas.progress_entry import ProgressEntryCreate


class ProgressService:
    def __init__(
        self,
        progress_repo: ProgressRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.progress_repo = progress_repo
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

    async def list_entries(
        self, client_id: uuid.UUID, current_user: User
    ) -> List[ProgressEntry]:
        await self._assert_can_access_client(client_id, current_user)
        return await self.progress_repo.list_by_client(client_id)

    async def create_entry(
        self, data: ProgressEntryCreate, current_user: User
    ) -> ProgressEntry:
        client = await self.clients_repo.get_by_user_id(current_user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
            )
        entry = ProgressEntry(
            client_id=client.id,
            type=data.type,
            date=data.date,
            weight=data.weight,
            measurements=data.measurements,
            photos=data.photos,
            notes=data.notes,
        )
        return await self.progress_repo.create(entry)
