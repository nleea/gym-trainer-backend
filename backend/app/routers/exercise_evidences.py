import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.dependencies import get_current_user
from app.dependencies import get_exercise_evidences_service
from app.models.user import User
from app.schemas.exercise_evidence import ExerciseEvidenceResponse
from app.services.exercise_evidences import ExerciseEvidencesService

router = APIRouter()

def _as_files_list(photos: Optional[List[UploadFile] | UploadFile]) -> List[UploadFile]:
    if photos is None:
        return []
    if isinstance(photos, list):
        return photos
    return [photos]


@router.post("", response_model=ExerciseEvidenceResponse, status_code=201)
async def create_evidence(
    training_log_id: uuid.UUID = Form(...),
    exercise_id: str = Form(...),
    exercise_name: str = Form(...),
    client_note: Optional[str] = Form(None),
    photos: Optional[List[UploadFile] | UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    service: ExerciseEvidencesService = Depends(get_exercise_evidences_service),
):
    return await service.create_evidence(
        training_log_id=training_log_id,
        exercise_id=exercise_id,
        exercise_name=exercise_name,
        client_note=client_note,
        photos=_as_files_list(photos),
        current_user=current_user,
    )


@router.get("/pending-count/{client_id}")
async def get_pending_count(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ExerciseEvidencesService = Depends(get_exercise_evidences_service),
):
    return await service.get_pending_counts(client_id, current_user)


@router.put("/{evidence_id}/feedback", response_model=ExerciseEvidenceResponse)
async def submit_feedback(
    evidence_id: uuid.UUID,
    trainer_feedback: Optional[str] = Form(None),
    trainer_rating: Optional[str] = Form(None),
    trainer_photo_urls: Optional[str] = Form(None),  # comma-separated URLs from client
    photos: Optional[List[UploadFile] | UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    service: ExerciseEvidencesService = Depends(get_exercise_evidences_service),
):
    existing_urls = [x.strip() for x in (trainer_photo_urls or "").split(",") if x.strip()]
    return await service.submit_feedback(
        evidence_id=evidence_id,
        trainer_feedback=trainer_feedback,
        trainer_rating=trainer_rating,
        photos=_as_files_list(photos),
        trainer_photo_urls=existing_urls,
        current_user=current_user,
    )


@router.put("/{evidence_id}/viewed", response_model=ExerciseEvidenceResponse)
async def mark_as_viewed(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ExerciseEvidencesService = Depends(get_exercise_evidences_service),
):
    return await service.mark_as_viewed(evidence_id, current_user)
