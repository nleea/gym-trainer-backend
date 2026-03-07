from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.models.exercise_evidence import ExerciseEvidence


class ExerciseEvidencesRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, evidence: ExerciseEvidence) -> ExerciseEvidence:
        pass

    @abstractmethod
    async def get_by_id(self, evidence_id: UUID) -> ExerciseEvidence | None:
        pass

    @abstractmethod
    async def get_by_log_and_exercise(
        self, training_log_id: UUID, exercise_id: str
    ) -> ExerciseEvidence | None:
        pass

    @abstractmethod
    async def list_by_training_log(self, training_log_id: UUID) -> List[ExerciseEvidence]:
        pass

    @abstractmethod
    async def list_by_client(
        self, client_id: UUID, limit: int = 20, offset: int = 0
    ) -> List[ExerciseEvidence]:
        pass

    @abstractmethod
    async def count_unanswered_by_client(self, client_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_unviewed_responded_by_client(self, client_id: UUID) -> int:
        pass

    @abstractmethod
    async def update(self, evidence: ExerciseEvidence, data: dict) -> ExerciseEvidence:
        pass
