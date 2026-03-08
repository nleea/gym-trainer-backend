import re
import uuid
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_trainer
from app.db.session import db_context
from app.models.user import User
from app.repositories.implementations.postgres.clients import ClientsRepository
from app.schemas.monthly_report import MonthlyReportResponse
from app.services.pdf_report import generate_monthly_report
from app.services.report_service import ReportService

router = APIRouter()

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _validate_month(month: str) -> str:
    if not _MONTH_RE.match(month):
        raise HTTPException(400, "month must be in YYYY-MM format (e.g. 2024-03)")
    return month


async def _resolve_client_id_for_user(
    client_id: uuid.UUID,
    current_user: User,
    clients_repo: ClientsRepository,
) -> None:
    """Raise 403/404 if current_user cannot access this client's reports."""
    client = await clients_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    if current_user.role == "trainer":
        if client.trainer_id != current_user.id:
            raise HTTPException(403, "Not authorized")
    else:
        # client role — only own data
        own = await clients_repo.get_by_user_id(current_user.id)
        if not own or own.id != client_id:
            raise HTTPException(403, "Not authorized")


# ── Trainer: raw data JSON ────────────────────────────────────────────────────

@router.get("/clients/{client_id}/monthly-report-data")
async def get_monthly_report_data(
    client_id: uuid.UUID,
    month: str = Query(..., description="YYYY-MM"),
    trainer: User = Depends(require_trainer),
    db: AsyncSession = Depends(db_context),
):
    _validate_month(month)
    clients_repo = ClientsRepository(db)
    client = await clients_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    if client.trainer_id != trainer.id:
        raise HTTPException(403, "Not authorized")

    service = ReportService()
    return await service.get_monthly_data(client_id, month, db)


# ── Trainer: generate PDF → upload to R2 + record + stream ───────────────────

@router.get("/clients/{client_id}/monthly-report")
async def download_monthly_report(
    client_id: uuid.UUID,
    month: str = Query(..., description="YYYY-MM"),
    trainer: User = Depends(require_trainer),
    db: AsyncSession = Depends(db_context),
):
    _validate_month(month)
    clients_repo = ClientsRepository(db)
    client = await clients_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    if client.trainer_id != trainer.id:
        raise HTTPException(403, "Not authorized")

    service = ReportService()
    data = await service.get_monthly_data(client_id, month, db)
    pdf_buffer: BytesIO = generate_monthly_report(data)

    # Upload to R2 and record (best-effort — don't fail the download if R2 is down)
    pdf_url = await service.upload_to_r2(pdf_buffer, client_id, month)
    try:
        await service.save_report_record(
            client_id=client_id,
            month=month,
            pdf_url=pdf_url,
            generated_by=str(trainer.id),
            db=db,
        )
    except Exception:
        pass  # duplicate key or DB issue — still stream the PDF

    client_name = data["client"]["name"].lower().replace(" ", "_")
    filename = f"report_{client_name}_{month}.pdf"
    pdf_buffer.seek(0)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Client: list own reports ──────────────────────────────────────────────────

@router.get("/clients/{client_id}/monthly-reports", response_model=List[MonthlyReportResponse])
async def list_monthly_reports(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_context),
):
    clients_repo = ClientsRepository(db)
    await _resolve_client_id_for_user(client_id, current_user, clients_repo)

    service = ReportService()
    reports = await service.list_reports(client_id, db)
    return [MonthlyReportResponse.model_validate(r) for r in reports]


# ── Client: download own report (re-generates on the fly) ────────────────────

@router.get("/clients/{client_id}/monthly-report/download")
async def client_download_report(
    client_id: uuid.UUID,
    month: str = Query(..., description="YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_context),
):
    _validate_month(month)
    clients_repo = ClientsRepository(db)
    await _resolve_client_id_for_user(client_id, current_user, clients_repo)

    service = ReportService()
    data = await service.get_monthly_data(client_id, month, db)
    pdf_buffer: BytesIO = generate_monthly_report(data)

    client_name = data["client"]["name"].lower().replace(" ", "_")
    filename = f"report_{client_name}_{month}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
