from sqlalchemy import URL, MetaData
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker


def get_session_maker(url: URL | str) -> async_sessionmaker:
    engine: AsyncEngine = create_async_engine(url=url, pool_pre_ping=True)
    return async_sessionmaker(engine, class_=AsyncSession)
