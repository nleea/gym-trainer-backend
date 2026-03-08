import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.core.dependencies import get_current_user
from app.dependencies import get_evidences_service
from app.models.user import User
from app.schemas.evidence import EvidenceItemResponse, EvidenceWeekResponse
from app.services.evidences import EvidencesService

router = APIRouter()

def _as_files_list(photos: Optional[list[UploadFile] | UploadFile]) -> list[UploadFile]:
    if photos is None:
        return []
    if isinstance(photos, list):
        return photos
    return [photos]


@router.get("", response_model=EvidenceWeekResponse)
async def list_evidences(
    client_id: uuid.UUID = Query(...),
    type: Optional[str] = Query(None),
    training_log_id: Optional[uuid.UUID] = Query(None),
    week_start: Optional[date] = Query(None),
    week_end: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=300),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: EvidencesService = Depends(get_evidences_service),
):
    return await service.list_evidences(
        client_id=client_id,
        current_user=current_user,
        evidence_type=type,
        training_log_id=training_log_id,
        week_start=week_start,
        week_end=week_end,
        limit=limit,
        offset=offset,
    )


@router.post("/nutrition", response_model=EvidenceItemResponse, status_code=201)
async def create_nutrition_evidence(
    taken_at: date = Form(...),
    photo: UploadFile = File(...),
    note: Optional[str] = Form(None),
    meal_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    service: EvidencesService = Depends(get_evidences_service),
):
    return await service.create_nutrition_evidence(
        current_user=current_user,
        taken_at=taken_at,
        file=photo,
        note=note,
        meal_name=meal_name,
    )


@router.put("/nutrition/{evidence_id}/feedback", response_model=EvidenceItemResponse)
async def submit_nutrition_feedback(
    evidence_id: uuid.UUID,
    trainer_feedback: Optional[str] = Form(None),
    trainer_rating: Optional[str] = Form(None),
    photos: Optional[list[UploadFile] | UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    service: EvidencesService = Depends(get_evidences_service),
):
    return await service.submit_nutrition_feedback(
        evidence_id=evidence_id,
        current_user=current_user,
        trainer_feedback=trainer_feedback,
        trainer_rating=trainer_rating,
        photos=_as_files_list(photos),
    )
