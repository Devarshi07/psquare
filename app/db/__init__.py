"""Database connection and session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.db.models import Base

settings = get_settings()


def get_async_engine():
    """Create async engine for PostgreSQL."""
    # Convert postgresql:// to postgresql+asyncpg://
    db_url = settings.database_url
    if db_url and "postgresql://" in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    return create_async_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.is_production is False,
    )


async_engine = get_async_engine()
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncSession:
    """Get a database session directly."""
    async with async_session_maker() as session:
        return session