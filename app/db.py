from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str, pool: bool = True) -> None:
        kwargs: dict = {}
        if url.startswith("sqlite"):
            # SQLite는 개발·테스트용이다. 연결을 풀에 두지 않아 이벤트 루프가 여러 개여도 안전하다.
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = NullPool
        elif pool:
            kwargs["pool_pre_ping"] = True
        else:
            kwargs["poolclass"] = NullPool
        self.engine: AsyncEngine = create_async_engine(url, **kwargs)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_all(self) -> None:
        from . import models  # noqa: F401  테이블 등록

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessionmaker() as session:
            yield session
