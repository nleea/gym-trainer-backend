import uuid
from typing import List
from fastapi import APIRouter, Depends
from app.core.dependencies import require_trainer
from app.dependencies import get_attendance_service
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceResponse, AttendanceUpdate
from app.services.attendance import AttendanceService

router = APIRouter()


@router.get("/trainer", response_model=List[AttendanceResponse])
async def list_attendance_by_trainer(
    trainer: User = Depends(require_trainer),
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.list_attendance_by_trainer(trainer)

@router.get("/{client_id}", response_model=List[AttendanceResponse])
async def list_attendance(
    client_id: uuid.UUID,
    trainer: User = Depends(require_trainer),
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.list_attendance(client_id, trainer)


@router.post("", response_model=AttendanceResponse, status_code=201)
async def create_attendance(
    data: AttendanceCreate,
    trainer: User = Depends(require_trainer),
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.create_attendance(data, trainer)


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: uuid.UUID,
    data: AttendanceUpdate,
    trainer: User = Depends(require_trainer),
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.update_attendance(attendance_id, data, trainer)
