import uuid
from typing import List

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.exercise_evidence import ExerciseEvidence
from app.repositories.interface.exerciseEvidencesInterface import (
    ExerciseEvidencesRepositoryInterface,
)


class ExerciseEvidencesRepository(ExerciseEvidencesRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, evidence: ExerciseEvidence) -> ExerciseEvidence:
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence

    async def get_by_id(self, evidence_id: uuid.UUID) -> ExerciseEvidence | None:
        result = await self.session.execute(
            select(ExerciseEvidence).where(ExerciseEvidence.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def get_by_log_and_exercise(
        self, training_log_id: uuid.UUID, exercise_id: str
    ) -> ExerciseEvidence | None:
        result = await self.session.execute(
            select(ExerciseEvidence).where(
                ExerciseEvidence.training_log_id == training_log_id,
                ExerciseEvidence.exercise_id == exercise_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_training_log(self, training_log_id: uuid.UUID) -> List[ExerciseEvidence]:
        result = await self.session.execute(
            select(ExerciseEvidence)
            .where(ExerciseEvidence.training_log_id == training_log_id)
            .order_by(ExerciseEvidence.submitted_at.desc(), ExerciseEvidence.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_client(
        self, client_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> List[ExerciseEvidence]:
        result = await self.session.execute(
            select(ExerciseEvidence)
            .where(ExerciseEvidence.client_id == client_id)
            .order_by(
                ExerciseEvidence.responded_at.is_(None).desc(),
                ExerciseEvidence.submitted_at.desc(),
                ExerciseEvidence.created_at.desc(),
            )
            .offset(max(offset, 0))
            .limit(max(limit, 1))
        )
        return list(result.scalars().all())

    async def count_unanswered_by_client(self, client_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ExerciseEvidence)
            .where(
                ExerciseEvidence.client_id == client_id,
                ExerciseEvidence.responded_at.is_(None),
            )
        )
        return int(result.scalar_one() or 0)

    async def count_unviewed_responded_by_client(self, client_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ExerciseEvidence)
            .where(
                ExerciseEvidence.client_id == client_id,
                ExerciseEvidence.responded_at.is_not(None),
                ExerciseEvidence.client_viewed_at.is_(None),
            )
        )
        return int(result.scalar_one() or 0)

    async def update(self, evidence: ExerciseEvidence, data: dict) -> ExerciseEvidence:
        for key, value in data.items():
            if value is not None:
                setattr(evidence, key, value)
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence
