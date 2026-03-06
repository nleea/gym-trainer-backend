from fastapi import APIRouter, Depends

from app.core.dependencies import require_trainer
from app.dependencies import get_auth_service
from app.models.user import User
from app.schemas.auth import (
    CreateClientRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    AuthResponse
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.register_trainer(data)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.refresh_token(data)


@router.post("/create-client", response_model=TokenResponse, status_code=201)
async def create_client(
    data: CreateClientRequest,
    trainer: User = Depends(require_trainer),
    service: AuthService = Depends(get_auth_service),
):
    return await service.create_client(data, trainer)
