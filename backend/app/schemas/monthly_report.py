import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MonthlyReportResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    month: str
    pdf_url: Optional[str]
    generated_at: datetime
    generated_by: str

    model_config = {"from_attributes": True}
