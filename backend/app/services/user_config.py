from app.models.user import User
from app.repositories.interface.userConfigInterface import UserConfigRepositoryInterface
from app.schemas.user_config import AppearanceConfigSchema, UserConfigResponse


class UserConfigService:
    def __init__(self, repo: UserConfigRepositoryInterface) -> None:
        self.repo = repo

    async def get_config(self, current_user: User) -> UserConfigResponse:
        user_id = str(current_user.id)
        record = await self.repo.get_by_user_id(user_id)
        if not record:
            return UserConfigResponse(
                user_id=user_id,
                config=AppearanceConfigSchema(),
            )
        return UserConfigResponse(
            user_id=user_id,
            config=AppearanceConfigSchema(**record.config),
        )

    async def save_config(
        self, body: AppearanceConfigSchema, current_user: User
    ) -> UserConfigResponse:
        user_id = str(current_user.id)
        await self.repo.upsert(user_id, body.model_dump())
        return UserConfigResponse(user_id=user_id, config=body)
