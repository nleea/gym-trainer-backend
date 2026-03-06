"""Seed script for development/testing.

Creates:
- 1 trainer user
- 2 client users linked to that trainer
- 1 training plan assigned to client 1
- 1 nutrition plan assigned to client 1
- Sample training logs and metrics for client 1

Usage:
    cd backend
    python -m scripts.seed
"""

import asyncio
import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.security import hash_password
from app.models.attendance import Attendance
from app.models.client import Client
from app.models.meal_log import MealLog
from app.models.metric import Metric
from app.models.nutrition_plan import NutritionPlan
from app.models.progress_entry import ProgressEntry  # noqa: F401 — registers model
from app.models.training_log import TrainingLog
from app.models.training_plan import TrainingPlan
from app.models.user import User


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("Creating trainer...")
        trainer = User(
            email="trainer@gymtrainer.com",
            name="Carlos Trainer",
            role="trainer",
            phone="+34 600 000 001",
            password_hash=hash_password("trainer123"),
        )
        session.add(trainer)
        await session.flush()

        print("Creating client users...")
        client_user_1 = User(
            email="client1@gymtrainer.com",
            name="Ana García",
            role="client",
            phone="+34 600 000 002",
            password_hash=hash_password("client123"),
        )
        client_user_2 = User(
            email="client2@gymtrainer.com",
            name="Luis Pérez",
            role="client",
            phone="+34 600 000 003",
            password_hash=hash_password("client123"),
        )
        session.add(client_user_1)
        session.add(client_user_2)
        await session.flush()

        print("Creating training plan...")
        training_plan = TrainingPlan(
            trainer_id=trainer.id,
            name="Plan Fuerza 12 Semanas",
            weeks=[
                {
                    "week": 1,
                    "days": [
                        {
                            "day": "Lunes",
                            "exercises": [
                                {"name": "Sentadilla", "sets": 4, "reps": 8, "weight": "60kg"},
                                {"name": "Press Banca", "sets": 4, "reps": 8, "weight": "50kg"},
                            ],
                        }
                    ],
                }
            ],
        )
        session.add(training_plan)
        await session.flush()

        print("Creating nutrition plan...")
        nutrition_plan = NutritionPlan(
            trainer_id=trainer.id,
            name="Plan Volumen 3000kcal",
            target_calories=3000,
            days=[
                {
                    "day": "Lunes",
                    "meals": [
                        {"type": "desayuno", "description": "Avena + plátano + proteína", "calories": 600},
                        {"type": "almuerzo", "description": "Pollo + arroz + verduras", "calories": 800},
                        {"type": "cena", "description": "Salmón + patata + ensalada", "calories": 700},
                    ],
                }
            ],
        )
        session.add(nutrition_plan)
        await session.flush()

        print("Creating client profiles...")
        client_1 = Client(
            user_id=client_user_1.id,
            trainer_id=trainer.id,
            status="active",
            start_date=date.today() - timedelta(days=30),
            goals="Ganar masa muscular y mejorar fuerza",
            weight=75.5,
            height=178.0,
            age=28,
            plan_id=training_plan.id,
            nutrition_plan_id=nutrition_plan.id,
        )
        client_2 = Client(
            user_id=client_user_2.id,
            trainer_id=trainer.id,
            status="active",
            start_date=date.today() - timedelta(days=15),
            goals="Perder grasa y mejorar resistencia",
            weight=88.0,
            height=182.0,
            age=35,
        )
        session.add(client_1)
        session.add(client_2)
        await session.flush()

        print("Creating training logs for client 1...")
        for i in range(7):
            log_date = date.today() - timedelta(days=i * 2)
            training_log = TrainingLog(
                client_id=client_1.id,
                trainer_id=trainer.id,
                date=log_date,
                duration=60,
                exercises=[
                    {"name": "Sentadilla", "sets": 4, "reps": 8, "weight": f"{60 + i * 2}kg"},
                    {"name": "Press Banca", "sets": 4, "reps": 8, "weight": f"{50 + i}kg"},
                    {"name": "Peso Muerto", "sets": 3, "reps": 6, "weight": f"{80 + i * 3}kg"},
                ],
            )
            session.add(training_log)

        print("Creating metrics for client 1...")
        for i in range(4):
            metric_date = date.today() - timedelta(weeks=i)
            metric = Metric(
                client_id=client_1.id,
                date=metric_date,
                weight_kg=75.5 - i * 0.3,
                body_fat_pct=18.0 - i * 0.2,
                muscle_pct=42.0 + i * 0.3,
                waist=82.0 - i * 0.5,
                arm=36.0 + i * 0.2,
                chest=98.0 + i * 0.3,
            )
            session.add(metric)

        print("Creating attendance records for client 1...")
        for i in range(10):
            att_date = date.today() - timedelta(days=i * 3)
            attendance = Attendance(
                client_id=client_1.id,
                trainer_id=trainer.id,
                date=att_date,
                attended=i % 5 != 0,  # Miss every 5th session
                notes="Sesión completada" if i % 5 != 0 else "No asistió",
            )
            session.add(attendance)

        print("Creating meal logs for client 1...")
        for i in range(3):
            meal_date = date.today() - timedelta(days=i)
            for meal_type, cal, prot in [
                ("desayuno", 550, 35.0),
                ("almuerzo", 750, 55.0),
                ("cena", 650, 45.0),
            ]:
                meal_log = MealLog(
                    client_id=client_1.id,
                    date=meal_date,
                    type=meal_type,
                    description=f"Comida de {meal_type}",
                    calories=cal,
                    protein=prot,
                )
                session.add(meal_log)

        await session.commit()

    print("\n✓ Seed completed successfully!")
    print("\nCredentials:")
    print("  Trainer: trainer@gymtrainer.com / trainer123")
    print("  Client 1: client1@gymtrainer.com / client123")
    print("  Client 2: client2@gymtrainer.com / client123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
