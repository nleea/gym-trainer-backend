from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_context

""" AUTH """
from app.repositories.implementations.postgres.auth import AuthRepository
from app.repositories.interface.authInterface import AuthRepositoryInterface
from app.services.auth import AuthService

""" CLIENTS """
from app.repositories.implementations.postgres.clients import ClientsRepository
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.services.clients import ClientsService

""" TRAINING PLANS """
from app.repositories.implementations.postgres.training_plans import TrainingPlansRepository
from app.repositories.interface.trainingPlansInterface import TrainingPlansRepositoryInterface
from app.services.training_plans import TrainingPlansService

""" NUTRITION PLANS """
from app.repositories.implementations.postgres.nutrition_plans import NutritionPlansRepository
from app.repositories.interface.nutritionPlansInterface import NutritionPlansRepositoryInterface
from app.services.nutrition_plans import NutritionPlansService

""" TRAINING LOGS """
from app.repositories.implementations.postgres.training_logs import TrainingLogsRepository
from app.repositories.interface.trainingLogsInterface import TrainingLogsRepositoryInterface
from app.services.training_logs import TrainingLogsService

""" MEAL LOGS """
from app.repositories.implementations.postgres.meal_logs import MealLogsRepository
from app.repositories.interface.mealLogsInterface import MealLogsRepositoryInterface
from app.services.meal_logs import MealLogsService

""" PROGRESS """
from app.repositories.implementations.postgres.progress import ProgressRepository
from app.repositories.interface.progressInterface import ProgressRepositoryInterface
from app.services.progress import ProgressService

""" METRICS """
from app.repositories.implementations.postgres.metrics import MetricsRepository
from app.repositories.interface.metricsInterface import MetricsRepositoryInterface
from app.services.metrics import MetricsService

""" EXERCISES """
from app.repositories.implementations.postgres.exercises import ExercisesRepository
from app.repositories.interface.exercisesInterface import ExercisesRepositoryInterface
from app.services.exercises import ExercisesService

""" ATTENDANCE """
from app.repositories.implementations.postgres.attendance import AttendanceRepository
from app.repositories.interface.attendanceInterface import AttendanceRepositoryInterface
from app.services.attendance import AttendanceService

""" USER CONFIG """
from app.repositories.implementations.postgres.user_config import UserConfigRepository
from app.repositories.interface.userConfigInterface import UserConfigRepositoryInterface
from app.services.user_config import UserConfigService

""" TRAINER DASHBOARD """
from app.repositories.implementations.postgres.trainer_dashboard_repo import TrainerDashboardRepository
from app.services.trainer_dashboard import TrainerDashboardService

""" WEEKLY CHECKIN """
from app.repositories.implementations.postgres.weekly_checkin import WeeklyCheckinRepository
from app.repositories.interface.weeklyCheckinInterface import WeeklyCheckinRepositoryInterface
from app.services.weekly_checkin import WeeklyCheckinService

""" PHOTOS """
from app.repositories.implementations.postgres.photo_repository import PhotoRepository
from app.repositories.interface.photoInterface import PhotoRepositoryInterface
from app.services.photo_service import PhotoService
from app.repositories.implementations.postgres.exercise_evidences import ExerciseEvidencesRepository
from app.repositories.interface.exerciseEvidencesInterface import ExerciseEvidencesRepositoryInterface
from app.services.exercise_evidences import ExerciseEvidencesService


# ── Repository factories ──────────────────────────────────────────────────────

async def get_auth_repository(db: AsyncSession = Depends(db_context)) -> AuthRepositoryInterface:
    return AuthRepository(db)

async def get_clients_repository(db: AsyncSession = Depends(db_context)) -> ClientsRepositoryInterface:
    return ClientsRepository(db)

async def get_training_plans_repository(db: AsyncSession = Depends(db_context)) -> TrainingPlansRepositoryInterface:
    return TrainingPlansRepository(db)

async def get_nutrition_plans_repository(db: AsyncSession = Depends(db_context)) -> NutritionPlansRepositoryInterface:
    return NutritionPlansRepository(db)

async def get_training_logs_repository(db: AsyncSession = Depends(db_context)) -> TrainingLogsRepositoryInterface:
    return TrainingLogsRepository(db)

async def get_meal_logs_repository(db: AsyncSession = Depends(db_context)) -> MealLogsRepositoryInterface:
    return MealLogsRepository(db)

async def get_progress_repository(db: AsyncSession = Depends(db_context)) -> ProgressRepositoryInterface:
    return ProgressRepository(db)

async def get_metrics_repository(db: AsyncSession = Depends(db_context)) -> MetricsRepositoryInterface:
    return MetricsRepository(db)

async def get_exercises_repository(db: AsyncSession = Depends(db_context)) -> ExercisesRepositoryInterface:
    return ExercisesRepository(db)

async def get_attendance_repository(db: AsyncSession = Depends(db_context)) -> AttendanceRepositoryInterface:
    return AttendanceRepository(db)

async def get_user_config_repository(db: AsyncSession = Depends(db_context)) -> UserConfigRepositoryInterface:
    return UserConfigRepository(db)


# ── Service factories ─────────────────────────────────────────────────────────

async def get_auth_service(
    auth_repo: AuthRepositoryInterface = Depends(get_auth_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> AuthService:
    return AuthService(auth_repo, clients_repo)

async def get_clients_service(
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
    metrics_repo: MetricsRepositoryInterface = Depends(get_metrics_repository),
    attendance_repo: AttendanceRepositoryInterface = Depends(get_attendance_repository),
    training_logs_repo: TrainingLogsRepositoryInterface = Depends(get_training_logs_repository),
    meal_logs_repo: MealLogsRepositoryInterface = Depends(get_meal_logs_repository),
) -> ClientsService:
    return ClientsService(clients_repo, metrics_repo, attendance_repo, training_logs_repo, meal_logs_repo)

async def get_training_plans_service(
    plans_repo: TrainingPlansRepositoryInterface = Depends(get_training_plans_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> TrainingPlansService:
    return TrainingPlansService(plans_repo, clients_repo)

async def get_nutrition_plans_service(
    plans_repo: NutritionPlansRepositoryInterface = Depends(get_nutrition_plans_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> NutritionPlansService:
    return NutritionPlansService(plans_repo, clients_repo)

async def get_training_logs_service(
    logs_repo: TrainingLogsRepositoryInterface = Depends(get_training_logs_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> TrainingLogsService:
    return TrainingLogsService(logs_repo, clients_repo)

async def get_meal_logs_service(
    logs_repo: MealLogsRepositoryInterface = Depends(get_meal_logs_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
    plans_repo: NutritionPlansRepositoryInterface = Depends(get_nutrition_plans_repository),
) -> MealLogsService:
    return MealLogsService(logs_repo, clients_repo, plans_repo)

async def get_progress_service(
    progress_repo: ProgressRepositoryInterface = Depends(get_progress_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> ProgressService:
    return ProgressService(progress_repo, clients_repo)

async def get_metrics_service(
    metrics_repo: MetricsRepositoryInterface = Depends(get_metrics_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> MetricsService:
    return MetricsService(metrics_repo, clients_repo)

async def get_exercises_service(
    exercises_repo: ExercisesRepositoryInterface = Depends(get_exercises_repository),
) -> ExercisesService:
    return ExercisesService(exercises_repo)

async def get_attendance_service(
    attendance_repo: AttendanceRepositoryInterface = Depends(get_attendance_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> AttendanceService:
    return AttendanceService(attendance_repo, clients_repo)

async def get_user_config_service(
    repo: UserConfigRepositoryInterface = Depends(get_user_config_repository),
) -> UserConfigService:
    return UserConfigService(repo)

async def get_trainer_dashboard_service(
    db: AsyncSession = Depends(db_context),
) -> TrainerDashboardService:
    return TrainerDashboardService(TrainerDashboardRepository(db))

async def get_weekly_checkin_repository(db: AsyncSession = Depends(db_context)) -> WeeklyCheckinRepositoryInterface:
    return WeeklyCheckinRepository(db)

async def get_weekly_checkin_service(
    checkin_repo: WeeklyCheckinRepositoryInterface = Depends(get_weekly_checkin_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> WeeklyCheckinService:
    return WeeklyCheckinService(checkin_repo, clients_repo)


async def get_photo_repository(db: AsyncSession = Depends(db_context)) -> PhotoRepositoryInterface:
    return PhotoRepository(db)


async def get_photo_service(
    photo_repo: PhotoRepositoryInterface = Depends(get_photo_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
) -> PhotoService:
    return PhotoService(photo_repo, clients_repo)


async def get_exercise_evidences_repository(
    db: AsyncSession = Depends(db_context),
) -> ExerciseEvidencesRepositoryInterface:
    return ExerciseEvidencesRepository(db)


async def get_exercise_evidences_service(
    evidences_repo: ExerciseEvidencesRepositoryInterface = Depends(get_exercise_evidences_repository),
    clients_repo: ClientsRepositoryInterface = Depends(get_clients_repository),
    training_logs_repo: TrainingLogsRepositoryInterface = Depends(get_training_logs_repository),
) -> ExerciseEvidencesService:
    return ExerciseEvidencesService(evidences_repo, clients_repo, training_logs_repo)
