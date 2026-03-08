import io
import uuid
from datetime import datetime
from typing import List, Optional

import boto3
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.exercise_evidence import ExerciseEvidence
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.exerciseEvidencesInterface import (
    ExerciseEvidencesRepositoryInterface,
)
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface


class ExerciseEvidencesService:
    _ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    _MAX_CLIENT_PHOTOS = 5
    _MAX_TRAINER_PHOTOS = 3

    def __init__(
        self,
        evidences_repo: ExerciseEvidencesRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
        training_logs_repo: TrainingLogsRepositoryInterface,
    ) -> None:
        self.evidences_repo = evidences_repo
        self.clients_repo = clients_repo
        self.training_logs_repo = training_logs_repo

    @staticmethod
    def _r2_endpoint() -> str:
        if settings.R2_ENDPOINT_URL:
            return settings.R2_ENDPOINT_URL.rstrip("/")
        if settings.R2_ACCOUNT_ID:
            return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        return ""

    @staticmethod
    def _assert_r2_configured() -> None:
        required = [
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
            settings.R2_BUCKET_NAME,
        ]
        if not all(required) or not ExerciseEvidencesService._r2_endpoint():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="R2 upload is not configured on server",
            )

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

    async def _assert_user_can_access_client(self, client_id: uuid.UUID, current_user: User):
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

    async def _assert_log_access(self, training_log_id: uuid.UUID, current_user: User):
        log = await self.training_logs_repo.get_by_id(training_log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training log not found")

        if current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(log.client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            own_client = await self.clients_repo.get_by_user_id(current_user.id)
            if not own_client or own_client.id != log.client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return log

    @staticmethod
    def _log_has_exercise(log_exercises, exercise_id: str) -> bool:
        for ex in (log_exercises or []):
            if not isinstance(ex, dict):
                continue
            ex_id = str(ex.get("exerciseId") or ex.get("exercise_id") or ex.get("id") or "")
            if ex_id == exercise_id:
                return True
        return False

    @staticmethod
    def _resize_image(data: bytes, content_type: str) -> bytes:
        try:
            from PIL import Image
        except Exception:
            return data

        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB") if content_type == "image/jpeg" else img
            max_side = max(img.size)
            if max_side > 1200:
                scale = 1200 / float(max_side)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            out = io.BytesIO()
            fmt = "JPEG" if content_type == "image/jpeg" else ("PNG" if content_type == "image/png" else "WEBP")
            save_kwargs = {"quality": 90} if fmt in {"JPEG", "WEBP"} else {}
            img.save(out, format=fmt, **save_kwargs)
            return out.getvalue()

    async def _upload_files(
        self,
        files: List[UploadFile],
        client_id: uuid.UUID,
        training_log_id: uuid.UUID,
        evidence_id: uuid.UUID,
        prefix: str,
    ) -> List[str]:
        self._assert_r2_configured()
        s3 = self._s3_client()
        bucket = str(settings.R2_BUCKET_NAME)
        keys: list[str] = []

        for idx, file in enumerate(files):
            content_type = (file.content_type or "").lower()
            if content_type not in self._ALLOWED_TYPES:
                raise HTTPException(status_code=422, detail="Only jpg, png and webp images are allowed")
            ext = self._ext_for_content_type(content_type)
            key = f"evidences/{client_id}/{training_log_id}/{evidence_id}/{prefix}_{idx + 1}.{ext}"

            raw = await file.read()
            payload = self._resize_image(raw, content_type)
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=payload,
                ContentType=content_type,
            )
            keys.append(key)
        return keys

    def _serialize_evidence(self, evidence: ExerciseEvidence) -> dict:
        data = evidence.model_dump()
        data["photo_urls"] = [self._signed_url(str(x)) for x in (evidence.photo_urls or [])]
        data["trainer_photo_urls"] = [
            self._signed_url(str(x)) for x in (evidence.trainer_photo_urls or [])
        ]
        return data

    async def create_evidence(
        self,
        training_log_id: uuid.UUID,
        exercise_id: str,
        exercise_name: str,
        client_note: Optional[str],
        photos: Optional[List[UploadFile]],
        current_user: User,
    ) -> dict:
        if current_user.role != "client":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client access required")

        log = await self._assert_log_access(training_log_id, current_user)
        if not self._log_has_exercise(log.exercises, exercise_id):
            raise HTTPException(status_code=400, detail="Exercise does not belong to the training log")

        if await self.evidences_repo.get_by_log_and_exercise(training_log_id, exercise_id):
            raise HTTPException(status_code=409, detail="Evidence already exists for this exercise")

        photos = photos or []
        if len(photos) > self._MAX_CLIENT_PHOTOS:
            raise HTTPException(status_code=422, detail="Maximum 5 photos per evidence")

        evidence_id = uuid.uuid4()
        photo_urls = await self._upload_files(
            photos,
            client_id=log.client_id,
            training_log_id=training_log_id,
            evidence_id=evidence_id,
            prefix="client",
        ) if photos else []

        evidence = ExerciseEvidence(
            id=evidence_id,
            training_log_id=training_log_id,
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            evidence_type="exercise",
            client_id=log.client_id,
            trainer_id=log.trainer_id,
            client_note=client_note,
            photo_urls=photo_urls,
            submitted_at=datetime.utcnow(),
        )
        created = await self.evidences_repo.create(evidence)
        return self._serialize_evidence(created)

    async def submit_feedback(
        self,
        evidence_id: uuid.UUID,
        trainer_feedback: Optional[str],
        trainer_rating: Optional[str],
        photos: Optional[List[UploadFile]],
        trainer_photo_urls: Optional[List[str]],
        current_user: User,
    ) -> dict:
        if current_user.role != "trainer":
            raise HTTPException(status_code=403, detail="Trainer access required")

        evidence = await self.evidences_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        if evidence.trainer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if evidence.responded_at is not None:
            raise HTTPException(status_code=409, detail="Feedback already submitted")
        if trainer_rating and trainer_rating not in {"correct", "improve"}:
            raise HTTPException(status_code=422, detail="Invalid trainer_rating")

        photos = photos or []
        if len(photos) > self._MAX_TRAINER_PHOTOS:
            raise HTTPException(status_code=422, detail="Maximum 3 photos for trainer feedback")

        uploaded = await self._upload_files(
            photos,
            client_id=evidence.client_id,
            training_log_id=evidence.training_log_id,
            evidence_id=evidence.id,
            prefix="trainer",
        ) if photos else []
        full_trainer_photos = (trainer_photo_urls or []) + uploaded

        updated = await self.evidences_repo.update(
            evidence,
            {
                "trainer_feedback": trainer_feedback,
                "trainer_rating": trainer_rating,
                "trainer_photo_urls": full_trainer_photos,
                "responded_at": datetime.utcnow(),
            },
        )
        return self._serialize_evidence(updated)

    async def mark_as_viewed(self, evidence_id: uuid.UUID, current_user: User) -> dict:
        if current_user.role != "client":
            raise HTTPException(status_code=403, detail="Client access required")
        evidence = await self.evidences_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        own_client = await self.clients_repo.get_by_user_id(current_user.id)
        if not own_client or own_client.id != evidence.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if evidence.client_viewed_at:
            return self._serialize_evidence(evidence)
        updated = await self.evidences_repo.update(
            evidence,
            {"client_viewed_at": datetime.utcnow()},
        )
        return self._serialize_evidence(updated)

    async def get_pending_counts(
        self, client_id: uuid.UUID, current_user: User
    ) -> dict:
        await self._assert_user_can_access_client(client_id, current_user)
        return {
            "unanswered": await self.evidences_repo.count_unanswered_by_client(client_id),
            "unviewed_responded": await self.evidences_repo.count_unviewed_responded_by_client(client_id),
        }
