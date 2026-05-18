from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from db.models import Base  # noqa: F401 — re-exported so callers can do `from db import Base`

async_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)

__all__ = ["async_engine", "AsyncSessionLocal", "sync_engine", "SyncSessionLocal", "Base"]
