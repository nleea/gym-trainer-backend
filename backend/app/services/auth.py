import uuid

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.client import Client
from app.models.user import User
from app.repositories.interface.authInterface import AuthRepositoryInterface
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
from app.schemas.auth import (
    CreateClientRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    AuthResponse
)


class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.auth_repo = auth_repo
        self.clients_repo = clients_repo

    def _make_tokens(self, user: User) -> TokenResponse:
        token_data = {"sub": str(user.id), "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def register_trainer(self, data: RegisterRequest) -> TokenResponse:
        existing = await self.auth_repo.get_user_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user = User(
            email=data.email,
            name=data.name,
            phone=data.phone,
            role="trainer",
            password_hash=hash_password(data.password),
        )
        user = await self.auth_repo.create_user(user)
        return self._make_tokens(user)

    async def login(self, data: LoginRequest) -> AuthResponse:
        user, client = await self.auth_repo.get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        tokens = self._make_tokens(user)
        return AuthResponse(
            user={**user.model_dump(), "client_id": client.id if client else None, 'plan': client.plan_id if client else None, 'nutriton_plan': client.nutrition_plan_id if client else None},
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )

    async def refresh_token(self, data: RefreshRequest) -> TokenResponse:
        payload = decode_token(data.refresh_token)
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = payload.get("sub")
        user = await self.auth_repo.get_user_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return self._make_tokens(user)

    async def create_client(self, data: CreateClientRequest, trainer: User) -> TokenResponse:
        existing = await self.auth_repo.get_user_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        client_user = User(
            email=data.email,
            name=data.name,
            phone=data.phone,
            role="client",
            password_hash=hash_password(data.password),
        )
        client_user = await self.auth_repo.create_user(client_user)

        client_profile = Client(
            user_id=client_user.id,
            trainer_id=trainer.id,
            status=data.status,
            goals=data.goals,
            weight=data.weight,
            height=data.height,
            age=data.age,
        )
        await self.clients_repo.create(client_profile)

        return self._make_tokens(client_user)
