from typing import AsyncGenerator
from typing import Callable, AsyncGenerator, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import get_settings
from app.core.config import settings, DatabaseType
from fastapi import Request

engine = create_async_engine(settings.DATABASE_URL, echo=False)


ContextDependency = Callable[..., AsyncGenerator[Any, None]]

def get_db_context() -> ContextDependency:
    """
    Returns the appropriate database context dependency based on configuration.
    For PostgreSQL: Returns a dependency that yields a database session
    """
    settings = get_settings()
    
    if settings.DATABASE_TYPE == DatabaseType.POSTGRES:
        async def get_postgres_context(request: Request) -> AsyncGenerator[AsyncSession, None]:
            async_session_factory = request.app.state.postgres_session
            async with async_session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        return get_postgres_context
    else:
        raise ValueError("Invalid DATABASE_TYPE")

db_context = get_db_context()