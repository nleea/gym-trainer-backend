import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Make app importable from alembic directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings  # noqa: E402

# Import all models so SQLModel registers them in metadata
from app.models.user import User  # noqa: F401, E402
from app.models.training_plan import TrainingPlan  # noqa: F401, E402
from app.models.nutrition_plan import NutritionPlan  # noqa: F401, E402
from app.models.client import Client  # noqa: F401, E402
from app.models.training_log import TrainingLog  # noqa: F401, E402
from app.models.meal_log import MealLog  # noqa: F401, E402
from app.models.progress_entry import ProgressEntry  # noqa: F401, E402
from app.models.attendance import Attendance  # noqa: F401, E402
from app.models.metric import Metric  # noqa: F401, E402
from app.models.user_session import UserSession  # noqa: F401, E402
from app.models.exercise import Exercise  # noqa: F401, E402
from app.models.exercise_evidence import ExerciseEvidence  # noqa: F401, E402
from app.models.exercise_favorite import ExerciseFavorite  # noqa: F401, E402
from app.models.monthly_report import MonthlyReport  # noqa: F401, E402
from app.models.photo import Photo  # noqa: F401, E402
from app.models.user_config import UserConfig  # noqa: F401, E402
from app.models.weekly_checkin import WeeklyCheckin  # noqa: F401, E402

config = context.config
fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    # Convert asyncpg URL to sync psycopg2-compatible URL for offline SQL generation
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run_migrations()
