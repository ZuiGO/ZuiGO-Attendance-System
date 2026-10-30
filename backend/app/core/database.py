"""Database configuration and asynchronous session factory with multi-tenant context."""

from contextvars import ContextVar
from typing import AsyncGenerator, Optional
import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings

# Context variable to hold tenant_id for the current request context
current_tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Asynchronous SQLAlchemy Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session scoped to current tenant."""
    async with AsyncSessionLocal() as session:
        tenant_id = current_tenant_id_ctx.get()
        if tenant_id:
            # Enforce Row-Level Security by setting the session-local tenant configuration
            await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
        try:
            yield session
        finally:
            await session.close()
