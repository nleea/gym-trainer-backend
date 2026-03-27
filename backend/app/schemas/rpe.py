from pydantic import BaseModel


class RPEHistoryItem(BaseModel):
    date: str        # 'YYYY-MM-DD'
    avg_rpe: float   # average RPE across all sets of the exercise that session
