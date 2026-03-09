import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    create_refresh_token_with_claims,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.client import Client
from app.models.user_session import UserSession
from app.models.user import User
from app.repositories.interface.authInterface import AuthRepositoryInterface
from app.repositories.interface.clientsInterface import ClientsRepositoryInterface
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


class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepositoryInterface,
        clients_repo: ClientsRepositoryInterface,
    ) -> None:
        self.auth_repo = auth_repo
        self.clients_repo = clients_repo

    async def _issue_tokens_for_session(
        self,
        user: User,
        *,
        device_name: str | None = None,
        device_info: str | None = None,
        existing_session: UserSession | None = None,
    ) -> TokenResponse:
        session_id = existing_session.id if existing_session else uuid.uuid4()
        token_data = {"sub": str(user.id), "role": user.role, "sid": str(session_id)}
        refresh_token, refresh_jti, refresh_exp = create_refresh_token_with_claims(token_data)

        session = existing_session or UserSession(
            id=session_id,
            user_id=user.id,
            refresh_jti=refresh_jti,
            device_name=(device_name or "").strip()[:120] or None,
            device_info=(device_info or "").strip()[:500] or None,
            expires_at=refresh_exp.replace(tzinfo=None),
            last_seen_at=datetime.utcnow(),
        )
        session.refresh_jti = refresh_jti
        session.expires_at = refresh_exp.replace(tzinfo=None)
        session.last_seen_at = datetime.utcnow()
        if device_name is not None:
            session.device_name = (device_name or "").strip()[:120] or None
        if device_info is not None:
            session.device_info = (device_info or "").strip()[:500] or None
        if session.revoked_at is not None:
            session.revoked_at = None

        if existing_session:
            await self.auth_repo.update_user_session(session)
        else:
            await self.auth_repo.create_user_session(session)

        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=refresh_token,
            session_id=str(session.id),
        )

    async def register_trainer(self, data: RegisterRequest) -> AuthResponse:
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
        tokens = await self._issue_tokens_for_session(user)
        return AuthResponse(
            user=user.model_dump(),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            session_id=tokens.session_id,
        )

    async def login(self, data: LoginRequest) -> AuthResponse:
        user, client = await self.auth_repo.get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        tokens = await self._issue_tokens_for_session(
            user,
            device_name=data.device_name,
            device_info=data.device_info,
        )
        return AuthResponse(
            user={**user.model_dump(), "client_id": client.id if client else None, 'plan': client.plan_id if client else None, 'nutriton_plan': client.nutrition_plan_id if client else None},
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            session_id=tokens.session_id,
        )

    async def refresh_token(self, data: RefreshRequest) -> TokenResponse:
        payload = decode_token(data.refresh_token)
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        jti = payload.get("jti")
        sid = payload.get("sid")
        if not jti or not sid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is missing session claims",
            )

        user_id = payload.get("sub")
        user = await self.auth_repo.get_user_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        session = await self.auth_repo.get_session_by_id(uuid.UUID(sid))
        if not session or session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found",
            )

        if session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked",
            )

        if session.refresh_jti != jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been rotated",
            )

        if session.expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
            )

        return await self._issue_tokens_for_session(
            user,
            device_name=data.device_name,
            device_info=data.device_info,
            existing_session=session,
        )

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

        return await self._issue_tokens_for_session(client_user)

    async def list_sessions(
        self,
        user: User,
        current_session_id: uuid.UUID | None,
    ) -> list[UserSessionResponse]:
        sessions = await self.auth_repo.list_active_sessions(user.id)
        items: list[UserSessionResponse] = []
        for s in sessions:
            items.append(
                UserSessionResponse(
                    id=str(s.id),
                    device_name=s.device_name,
                    device_info=s.device_info,
                    ip_address=s.ip_address,
                    created_at=s.created_at.replace(tzinfo=timezone.utc).isoformat(),
                    last_seen_at=s.last_seen_at.replace(tzinfo=timezone.utc).isoformat(),
                    expires_at=s.expires_at.replace(tzinfo=timezone.utc).isoformat(),
                    is_current=bool(current_session_id and s.id == current_session_id),
                )
            )
        return items

    async def revoke_session(self, user: User, session_id: uuid.UUID) -> None:
        session = await self.auth_repo.get_session_by_id(session_id)
        if not session or session.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.revoked_at is None:
            session.revoked_at = datetime.utcnow()
            await self.auth_repo.update_user_session(session)

    async def logout_current_session(self, user: User, current_session_id: uuid.UUID | None) -> None:
        if not current_session_id:
            return
        session = await self.auth_repo.get_session_by_id(current_session_id)
        if session and session.user_id == user.id and session.revoked_at is None:
            session.revoked_at = datetime.utcnow()
            await self.auth_repo.update_user_session(session)

    async def logout_all_sessions(
        self,
        user: User,
        current_session_id: uuid.UUID | None,
        data: LogoutAllRequest,
    ) -> int:
        sessions = await self.auth_repo.list_active_sessions(user.id)
        revoked = 0
        for session in sessions:
            if data.keep_current and current_session_id and session.id == current_session_id:
                continue
            if session.revoked_at is None:
                session.revoked_at = datetime.utcnow()
                await self.auth_repo.update_user_session(session)
                revoked += 1
        return revoked
