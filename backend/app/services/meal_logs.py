import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status

from app.models.meal_log import MealLog
from app.models.user import User
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.repositories.interface.mealLogsInterface import MealLogsRepositoryInterface
from app.repositories.interface.nutritionPlansInterface import NutritionPlansRepositoryInterface
from app.schemas.meal_log import (
    MealLogCreate,
    MealLogUpsert,
    Adherence,
    DailyAdherence,
    MacroProgress,
    NutritionSummaryResponse,
    TodayMacros,
)


class MealLogsService:
    def __init__(
        self,
        logs_repo: MealLogsRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
        plans_repo: Optional[NutritionPlansRepositoryInterface] = None,
    ) -> None:
        self.logs_repo = logs_repo
        self.clients_repo = clients_repo
        self.plans_repo = plans_repo

    async def _get_client_for_user(self, user: User):
        client = await self.clients_repo.get_by_user_id(user.id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client profile not found",
            )
        return client

    async def _assert_client_access(self, client_id: uuid.UUID, current_user: User):
        if current_user.role == "client":
            client = await self._get_client_for_user(current_user)
            if client.id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return client
        elif current_user.role == "trainer":
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return client
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def list_logs(
        self,
        current_user: User,
        client_id: Optional[uuid.UUID] = None,
        log_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[MealLog]:
        if current_user.role == "client":
            client = await self._get_client_for_user(current_user)
            client_id = client.id
        elif current_user.role == "trainer" and client_id:
            client = await self.clients_repo.get_by_id(client_id)
            if not client or client.trainer_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return await self.logs_repo.list_by_filters(
            client_id=client_id,
            log_date=log_date,
            start_date=start_date,
            end_date=end_date,
        )

    async def create_log(self, data: MealLogCreate, current_user: User) -> MealLog:
        client = await self._get_client_for_user(current_user)
        log = MealLog(
            client_id=client.id,
            date=data.date,
            type=data.type,
            meal_name=data.meal_name,
            meal_key=data.meal_key,
            description=data.description,
            calories=data.calories,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
            fiber=data.fiber,
            water_ml=data.water_ml,
            foods=data.foods,
            notes=data.notes,
        )
        return await self.logs_repo.create(log)

    async def upsert_log(self, data: MealLogUpsert, current_user: User) -> MealLog:
        """Atomic upsert by client+date+meal_key using INSERT ON CONFLICT."""
        client = await self._get_client_for_user(current_user)

        log = MealLog(
            client_id=client.id,
            date=data.date,
            type=data.type,
            meal_name=data.meal_name,
            meal_key=data.meal_key,
            description=data.description,
            calories=data.calories,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
            fiber=data.fiber,
            water_ml=data.water_ml,
            foods=data.foods,
            notes=data.notes,
        )

        if data.meal_key:
            return await self.logs_repo.upsert_by_client_date_meal_key(log)

        return await self.logs_repo.create(log)

    async def delete_log(self, log_id: uuid.UUID, current_user: User) -> None:
        log = await self.logs_repo.get_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meal log not found"
            )
        client = await self._get_client_for_user(current_user)
        if log.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await self.logs_repo.delete(log)

    async def get_nutrition_summary(
        self,
        client_id: uuid.UUID,
        summary_date: date,
        current_user: User,
    ) -> NutritionSummaryResponse:
        await self._assert_client_access(client_id, current_user)

        # Today's logs
        today_logs = await self.logs_repo.list_by_filters(
            client_id=client_id, log_date=summary_date
        )

        # Last 30 days for adherence
        start_30 = summary_date - timedelta(days=29)
        recent_logs = await self.logs_repo.list_by_filters(
            client_id=client_id, start_date=start_30, end_date=summary_date
        )

        # Get plan targets
        target_calories = 0
        target_protein = 0.0
        target_carbs = 0.0
        target_fat = 0.0
        target_water = 0

        if self.plans_repo:
            client = await self.clients_repo.get_by_id(client_id)
            if client and client.nutrition_plan_id:
                plan = await self.plans_repo.get_by_id(client.nutrition_plan_id)
                if plan:
                    target_calories = plan.target_calories or 0
                    target_protein = plan.target_protein or 0.0
                    target_carbs = plan.target_carbs or 0.0
                    target_fat = plan.target_fat or 0.0
                    target_water = plan.water_ml or 0

        # Consumed today (exclude water entry)
        meal_logs = [l for l in today_logs if l.meal_key != "daily_water"]
        water_log = next((l for l in today_logs if l.meal_key == "daily_water"), None)

        consumed_cal = sum(l.calories or 0 for l in meal_logs)
        consumed_prot = sum(l.protein or 0.0 for l in meal_logs)
        consumed_carbs = sum(l.carbs or 0.0 for l in meal_logs)
        consumed_fat = sum(l.fat or 0.0 for l in meal_logs)
        consumed_water = water_log.water_ml if water_log else 0

        today_macros = TodayMacros(
            calories=MacroProgress(consumed=consumed_cal, target=target_calories),
            protein_g=MacroProgress(consumed=consumed_prot, target=target_protein),
            carbs_g=MacroProgress(consumed=consumed_carbs, target=target_carbs),
            fat_g=MacroProgress(consumed=consumed_fat, target=target_fat),
            water_ml=MacroProgress(consumed=consumed_water or 0, target=target_water),
        )

        # Adherence
        dates_with_logs: set[str] = set()
        for l in recent_logs:
            if l.meal_key != "daily_water":
                dates_with_logs.add(l.date.isoformat())

        last_7_days = sum(
            1 for i in range(7)
            if (summary_date - timedelta(days=i)).isoformat() in dates_with_logs
        )
        last_30_days = len(dates_with_logs)
        adherence_pct = round((last_30_days / 30) * 100)

        adherence = Adherence(
            last_7_days=last_7_days,
            last_30_days=last_30_days,
            percentage=adherence_pct,
        )

        # Daily history for chart (last 30 days)
        daily_history: list[DailyAdherence] = []
        for i in range(29, -1, -1):
            d = summary_date - timedelta(days=i)
            dstr = d.isoformat()
            day_logs = [l for l in recent_logs if l.date.isoformat() == dstr and l.meal_key != "daily_water"]
            has_log = len(day_logs) > 0
            cal_consumed = sum(l.calories or 0 for l in day_logs)
            cal_pct = min(100.0, (cal_consumed / target_calories * 100)) if target_calories else (100.0 if has_log else 0.0)
            daily_history.append(DailyAdherence(date=dstr, has_log=has_log, calories_pct=cal_pct))

        return NutritionSummaryResponse(
            today_logs=today_logs,
            today_macros=today_macros,
            adherence=adherence,
            daily_history=daily_history,
        )
