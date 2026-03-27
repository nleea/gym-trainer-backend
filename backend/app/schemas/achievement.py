import uuid
from typing import List, Optional

from pydantic import BaseModel


class AchievementItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str
    icon: str
    category: str
    unlocked: bool
    unlocked_at: Optional[str] = None
    progress: int
    target: int


class AchievementSummaryLatest(BaseModel):
    slug: str
    title: str
    icon: str
    unlocked_at: str


class AchievementSummaryResponse(BaseModel):
    total: int
    unlocked: int
    latest: List[AchievementSummaryLatest]
