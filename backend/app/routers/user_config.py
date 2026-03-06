from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.dependencies import get_user_config_service
from app.models.user import User
from app.schemas.user_config import AppearanceConfigSchema, UserConfigResponse
from app.services.user_config import UserConfigService

router = APIRouter()


@router.get("/", response_model=UserConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user),
    service: UserConfigService = Depends(get_user_config_service),
):
    return await service.get_config(current_user)


@router.put("/", response_model=UserConfigResponse)
async def save_config(
    body: AppearanceConfigSchema,
    current_user: User = Depends(get_current_user),
    service: UserConfigService = Depends(get_user_config_service),
):
    return await service.save_config(body, current_user)
