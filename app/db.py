from collections.abc import AsyncIterator

from sqlalchemy import String, inspect, text
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
            await conn.run_sync(_add_missing_columns)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessionmaker() as session:
            yield session


def _add_missing_columns(sync_conn) -> None:
    """create_all은 이미 있는 테이블에 칸을 더하지 않는다. 모델에 새로 생긴 문자열 칸을 기본값 ''로 붙인다."""
    # ponytail: 문자열 칸만 자동으로 붙인다. 다른 타입이 필요해지면 Alembic을 들인다.
    insp = inspect(sync_conn)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            if not isinstance(col.type, String):
                raise RuntimeError(f"{table.name}.{col.name}: 문자열이 아닌 새 칸은 직접 마이그레이션해야 해요")
            ddl = col.type.compile(dialect=sync_conn.dialect)
            sync_conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl} NOT NULL DEFAULT ''"))
