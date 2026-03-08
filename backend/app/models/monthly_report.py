import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class MonthlyReport(SQLModel, table=True):
    __tablename__ = "monthly_reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    month: str = Field(max_length=7, index=True)  # "2024-03"
    pdf_url: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(max_length=100, default="auto")  # "auto" | trainer UUID str
