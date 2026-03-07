from typing import List, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from enum import Enum


class DatabaseType(str, Enum):
    POSTGRES = "postgres"
    DYNAMODB = "dynamodb"

class Settings(BaseSettings):
    # Database
    DATABASE_TYPE: DatabaseType = DatabaseType.POSTGRES
    DATABASE_URL: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "gym_db"

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Cloudflare R2
    R2_ACCOUNT_ID: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET_NAME: str | None = None
    R2_ENDPOINT_URL: str | None = None
    R2_PUBLIC_BASE_URL: str | None = None
    R2_UPLOAD_URL_EXPIRES: int = 900

    # External APIs
    RAPIDAPI_KEY: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
