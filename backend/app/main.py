from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, DatabaseType
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.init_db import init_db
from app.routers import (
    attendance,
    auth,
    clients,
    evidences,
    exercises,
    meal_logs,
    metrics,
    nutrition_plans,
    progress,
    training_logs,
    training_plans,
    exercise_evidences,
)
from app.routers import user_config
from app.routers import wellness
from app.routers import weekly_checkin
from app.routers import trainer_dashboard
from app.routers import photos
from app.routers import monthly_report
from app.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    settings = get_settings()
    
    if settings.DATABASE_TYPE == DatabaseType.POSTGRES:
        engine = create_async_engine(
            settings.DATABASE_URL, 
            echo=True, future=True,     
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        app.state.postgres_session = async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        app.state.engine = engine
    
    await init_db()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="My Gym Trainer API",
    version="1.0.0",
    description="Backend API for the My Gym Trainer PWA",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
app.include_router(training_plans.router, prefix="/training-plans", tags=["training-plans"])
app.include_router(nutrition_plans.router, prefix="/nutrition-plans", tags=["nutrition-plans"])
app.include_router(training_logs.router, prefix="/training-logs", tags=["training-logs"])
app.include_router(meal_logs.router, prefix="/meal-logs", tags=["meal-logs"])
app.include_router(progress.router, prefix="/progress", tags=["progress"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(user_config.router, prefix="/config", tags=["config"])
app.include_router(weekly_checkin.router, prefix="/checkins", tags=["checkins"])
app.include_router(trainer_dashboard.router, prefix="/trainer", tags=["trainer-dashboard"])
app.include_router(photos.router, prefix="/photos", tags=["photos"])
app.include_router(exercise_evidences.router, prefix="/exercise-evidences", tags=["exercise-evidences"])
app.include_router(evidences.router, prefix="/evidences", tags=["evidences"])
app.include_router(monthly_report.router, tags=["monthly-report"])
app.include_router(wellness.router, prefix="/wellness", tags=["wellness"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
