import uuid

from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import get_current_session_id, get_current_user
from app.core.dependencies import require_trainer
from app.dependencies import get_auth_service
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    CreateClientRequest,
    LoginRequest,
    LogoutAllRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserSessionResponse,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
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


@router.get("/sessions", response_model=list[UserSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id),
    service: AuthService = Depends(get_auth_service),
):
    return await service.list_sessions(current_user, current_session_id)


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    await service.revoke_session(current_user, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout", status_code=204)
async def logout_current(
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout_current_session(current_user, current_session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all")
async def logout_all(
    data: LogoutAllRequest,
    current_user: User = Depends(get_current_user),
    current_session_id: uuid.UUID | None = Depends(get_current_session_id),
    service: AuthService = Depends(get_auth_service),
):
    revoked = await service.logout_all_sessions(current_user, current_session_id, data)
    return {"revoked": revoked}
