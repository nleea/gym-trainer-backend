from sqlmodel import SQLModel

from app.db.session import engine

# Import all models so SQLModel registers them in metadata
from app.models.user import User  # noqa: F401
from app.models.training_plan import TrainingPlan  # noqa: F401
from app.models.nutrition_plan import NutritionPlan  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.training_log import TrainingLog  # noqa: F401
from app.models.meal_log import MealLog  # noqa: F401
from app.models.progress_entry import ProgressEntry  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.metric import Metric  # noqa: F401
from app.models.exercise import Exercise  # noqa: F401
from app.models.user_config import UserConfig  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
