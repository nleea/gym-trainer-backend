"""
APScheduler: auto-generates monthly PDF reports at end of each month.
Saves to R2 (if configured) and records in monthly_reports table.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger(day="last", hour=23, minute=55))
async def auto_generate_monthly_reports():
    """Runs at 23:55 on the last day of each month."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlmodel import select

    from app.core.config import settings
    from app.models.client import Client
    from app.services.pdf_report import generate_monthly_report
    from app.services.report_service import ReportService

    month = datetime.now().strftime("%Y-%m")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    report_service = ReportService()
    processed = 0
    failed = 0

    async with session_factory() as db:
        clients_result = await db.execute(
            select(Client).where(Client.status == "active")
        )
        clients = list(clients_result.scalars().all())
        logger.info(f"[scheduler] Auto-generating reports for {len(clients)} active clients, month={month}")

        for client in clients:
            try:
                data = await report_service.get_monthly_data(client.id, month, db)
                pdf_buffer = generate_monthly_report(data)
                pdf_url = await report_service.upload_to_r2(pdf_buffer, client.id, month)
                await report_service.save_report_record(
                    client_id=client.id,
                    month=month,
                    pdf_url=pdf_url,
                    generated_by="auto",
                    db=db,
                )
                processed += 1
            except Exception as e:
                logger.error(f"[scheduler] Failed report for client {client.id}: {e}")
                failed += 1
                continue

    await engine.dispose()
    logger.info(f"[scheduler] Done. processed={processed}, failed={failed}")
