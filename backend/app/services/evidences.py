import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date, datetime
from typing import Optional

import boto3
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.exercise_evidence import ExerciseEvidence
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.exerciseEvidencesInterface import (
    ExerciseEvidencesRepositoryInterface,
)
from app.schemas.evidence import EvidenceDayResponse, EvidenceItemResponse, EvidenceWeekResponse

logger = logging.getLogger(__name__)


class EvidenceProvider(ABC):
    type_name: str

    @abstractmethod
    async def list_items(
        self,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID,
        training_log_id: Optional[uuid.UUID],
        week_start: Optional[date],
        week_end: Optional[date],
        limit: int,
        offset: int,
    ) -> list[EvidenceItemResponse]:
        pass


class BaseExerciseEvidenceProvider(EvidenceProvider):
    def __init__(self, exercise_repo: ExerciseEvidencesRepositoryInterface, sign_url, evidence_type: str):
        self.exercise_repo = exercise_repo
        self.sign_url = sign_url
        self.type_name = evidence_type

    def _safe_photo_url(self, key_or_url: str) -> str:
        try:
            return self.sign_url(key_or_url)
        except Exception:
            logger.exception("Failed to sign evidence URL")
            return key_or_url if key_or_url.startswith(("http://", "https://")) else ""

    def _to_response(self, row: ExerciseEvidence) -> EvidenceItemResponse:
        urls = [self._safe_photo_url(str(x)) for x in (row.photo_urls or [])]
        urls = [u for u in urls if u]
        trainer_urls = [self._safe_photo_url(str(x)) for x in (row.trainer_photo_urls or [])]
        trainer_urls = [u for u in trainer_urls if u]
        item_date = row.nutrition_date if row.evidence_type == "nutrition" and row.nutrition_date else row.submitted_at.date()
        return EvidenceItemResponse(
            id=row.id,
            training_log_id=row.training_log_id,
            exercise_id=row.exercise_id,
            client_id=row.client_id,
            trainer_id=row.trainer_id,
            type=row.evidence_type,
            date=item_date,
            exercise_name=row.exercise_name,
            client_note=row.client_note,
            photo_urls=urls,
            submitted_at=row.submitted_at,
            trainer_feedback=row.trainer_feedback,
            trainer_rating=row.trainer_rating,
            trainer_photo_urls=trainer_urls,
            responded_at=row.responded_at,
            client_viewed_at=row.client_viewed_at,
            created_at=row.created_at,
        )

    async def list_items(
        self,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID,
        training_log_id: Optional[uuid.UUID],
        week_start: Optional[date],
        week_end: Optional[date],
        limit: int,
        offset: int,
    ) -> list[EvidenceItemResponse]:
        if training_log_id:
            rows = await self.exercise_repo.list_by_training_log(training_log_id)
            rows = [r for r in rows if r.client_id == client_id and r.evidence_type == self.type_name]
        else:
            rows = await self.exercise_repo.list_by_client_filtered(
                client_id=client_id,
                week_start=week_start,
                week_end=week_end,
                evidence_type=self.type_name,
                limit=limit,
                offset=offset,
            )
        return [self._to_response(r) for r in rows]


class EvidencesService:
    _ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    _MAX_TRAINER_PHOTOS = 3

    def __init__(
        self,
        clients_repo: ClientsRepositoryInterface,
        exercise_repo: ExerciseEvidencesRepositoryInterface,
        providers: list[EvidenceProvider],
    ):
        self.clients_repo = clients_repo
        self.exercise_repo = exercise_repo
        self.providers_map = {p.type_name: p for p in providers}

    @staticmethod
    def _r2_endpoint() -> str:
        if settings.R2_ENDPOINT_URL:
            return settings.R2_ENDPOINT_URL.rstrip("/")
        if settings.R2_ACCOUNT_ID:
            return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        return ""

    def _s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url=self._r2_endpoint(),
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    def _signed_url(self, key_or_url: str, expires: int = 3600) -> str:
        if key_or_url.startswith("http://") or key_or_url.startswith("https://"):
            return key_or_url
        return self._s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key_or_url},
            ExpiresIn=expires,
        )

    @staticmethod
    def _ext_for_content_type(content_type: str) -> str:
        mapping = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        return mapping.get(content_type, "jpg")

    async def _assert_access(self, client_id: uuid.UUID, current_user: User):
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
        return client

    async def _upload_files(
        self,
        files: list[UploadFile],
        *,
        client_id: uuid.UUID,
        evidence_id: uuid.UUID,
        folder: str,
        prefix: str,
    ) -> list[str]:
        s3 = self._s3_client()
        bucket = str(settings.R2_BUCKET_NAME)
        keys: list[str] = []
        for idx, file in enumerate(files):
            content_type = (file.content_type or "").lower()
            if content_type not in self._ALLOWED_TYPES:
                raise HTTPException(status_code=422, detail="Only jpg, png and webp images are allowed")
            ext = self._ext_for_content_type(content_type)
            key = f"evidences/{client_id}/{folder}/{evidence_id}/{prefix}_{idx + 1}.{ext}"
            payload = await file.read()
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=payload,
                ContentType=content_type,
            )
            keys.append(key)
        return keys

    async def create_nutrition_evidence(
        self,
        current_user: User,
        taken_at: date,
        file: UploadFile,
        note: Optional[str] = None,
        meal_name: Optional[str] = None,
    ) -> EvidenceItemResponse:
        if current_user.role != "client":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client access required")

        own_client = await self.clients_repo.get_by_user_id(current_user.id)
        if not own_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        evidence_id = uuid.uuid4()
        uploaded = await self._upload_files(
            [file],
            client_id=own_client.id,
            evidence_id=evidence_id,
            folder="nutrition",
            prefix="client",
        )
        client_note = f"Comida: {meal_name} - {note}" if meal_name and note else (f"Comida: {meal_name}" if meal_name else note)

        created = await self.exercise_repo.create(
            ExerciseEvidence(
                id=evidence_id,
                evidence_type="nutrition",
                nutrition_date=taken_at,
                training_log_id=None,
                exercise_id=None,
                exercise_name=meal_name or "Food evidence",
                client_id=own_client.id,
                trainer_id=own_client.trainer_id,
                client_note=client_note,
                photo_urls=uploaded,
                submitted_at=datetime.utcnow(),
            )
        )

        return EvidenceItemResponse(
            id=created.id,
            training_log_id=None,
            exercise_id=None,
            client_id=created.client_id,
            trainer_id=created.trainer_id,
            type="nutrition",
            date=created.nutrition_date or created.submitted_at.date(),
            exercise_name=created.exercise_name,
            client_note=created.client_note,
            photo_urls=[self._signed_url(str(x)) for x in (created.photo_urls or [])],
            submitted_at=created.submitted_at,
            trainer_feedback=created.trainer_feedback,
            trainer_rating=created.trainer_rating,
            trainer_photo_urls=[self._signed_url(str(x)) for x in (created.trainer_photo_urls or [])],
            responded_at=created.responded_at,
            client_viewed_at=created.client_viewed_at,
            created_at=created.created_at,
        )

    async def submit_nutrition_feedback(
        self,
        evidence_id: uuid.UUID,
        current_user: User,
        trainer_feedback: Optional[str] = None,
        trainer_rating: Optional[str] = None,
        photos: Optional[list[UploadFile]] = None,
    ) -> EvidenceItemResponse:
        if current_user.role != "trainer":
            raise HTTPException(status_code=403, detail="Trainer access required")
        if trainer_rating and trainer_rating not in {"correct", "improve"}:
            raise HTTPException(status_code=422, detail="Invalid trainer_rating")

        evidence = await self.exercise_repo.get_by_id(evidence_id)
        if not evidence or evidence.evidence_type != "nutrition":
            raise HTTPException(status_code=404, detail="Evidence not found")
        if evidence.trainer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if evidence.responded_at is not None:
            raise HTTPException(status_code=409, detail="Feedback already submitted")

        photos = photos or []
        if len(photos) > self._MAX_TRAINER_PHOTOS:
            raise HTTPException(status_code=422, detail="Maximum 3 photos for trainer feedback")

        uploaded = await self._upload_files(
            photos,
            client_id=evidence.client_id,
            evidence_id=evidence.id,
            folder="nutrition",
            prefix="trainer",
        ) if photos else []
        full_trainer_photos = (evidence.trainer_photo_urls or []) + uploaded

        updated = await self.exercise_repo.update(
            evidence,
            {
                "trainer_feedback": trainer_feedback,
                "trainer_rating": trainer_rating,
                "trainer_photo_urls": full_trainer_photos,
                "responded_at": datetime.utcnow(),
            },
        )

        return EvidenceItemResponse(
            id=updated.id,
            training_log_id=updated.training_log_id,
            exercise_id=updated.exercise_id,
            client_id=updated.client_id,
            trainer_id=updated.trainer_id,
            type=updated.evidence_type,
            date=updated.nutrition_date or updated.submitted_at.date(),
            exercise_name=updated.exercise_name,
            client_note=updated.client_note,
            photo_urls=[self._signed_url(str(x)) for x in (updated.photo_urls or [])],
            submitted_at=updated.submitted_at,
            trainer_feedback=updated.trainer_feedback,
            trainer_rating=updated.trainer_rating,
            trainer_photo_urls=[self._signed_url(str(x)) for x in (updated.trainer_photo_urls or [])],
            responded_at=updated.responded_at,
            client_viewed_at=updated.client_viewed_at,
            created_at=updated.created_at,
        )

    async def list_evidences(
        self,
        client_id: uuid.UUID,
        current_user: User,
        evidence_type: Optional[str] = None,
        training_log_id: Optional[uuid.UUID] = None,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> EvidenceWeekResponse:
        client = await self._assert_access(client_id, current_user)
        if week_start and week_end and week_start > week_end:
            week_start, week_end = week_end, week_start

        if evidence_type:
            provider = self.providers_map.get(evidence_type)
            if not provider:
                raise HTTPException(status_code=422, detail=f"Unsupported evidence type: {evidence_type}")
            providers = [provider]
        else:
            providers = list(self.providers_map.values())

        items: list[EvidenceItemResponse] = []
        for provider in providers:
            items.extend(
                await provider.list_items(
                    client_id=client_id,
                    trainer_id=client.trainer_id,
                    training_log_id=training_log_id,
                    week_start=week_start,
                    week_end=week_end,
                    limit=limit,
                    offset=offset,
                )
            )

        items.sort(key=lambda x: (x.date, x.submitted_at), reverse=True)
        grouped: dict[date, list[EvidenceItemResponse]] = defaultdict(list)
        for item in items:
            grouped[item.date].append(item)

        days = [
            EvidenceDayResponse(
                date=day_date,
                label=day_date.strftime("%A"),
                evidences=day_items,
            )
            for day_date, day_items in sorted(grouped.items(), reverse=True)
            if day_items
        ]
        return EvidenceWeekResponse(week_start=week_start, week_end=week_end, days=days)

    def build_nutrition_provider(self, exercise_repo: ExerciseEvidencesRepositoryInterface) -> BaseExerciseEvidenceProvider:
        return BaseExerciseEvidenceProvider(exercise_repo, self._signed_url, "nutrition")

    def build_exercise_provider(
        self, exercise_repo: ExerciseEvidencesRepositoryInterface
    ) -> BaseExerciseEvidenceProvider:
        return BaseExerciseEvidenceProvider(exercise_repo, self._signed_url, "exercise")
