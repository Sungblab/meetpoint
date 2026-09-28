import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import event

from .broker import Broker
from .config import Settings, get_settings
from .db import Database
from .matching.ai import AIClient
from .matching.service import MatchingService, purge_expired_rooms
from .routes import api, host, pages
from .web import BASE_DIR, Services

log = logging.getLogger("meetpoint")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    db = Database(settings.database_url, pool=settings.database_pool)
    if settings.database_url.startswith("sqlite"):

        @event.listens_for(db.engine.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()

    broker = Broker()
    ai = AIClient(settings) if settings.ai_enabled else None
    matching = MatchingService(db, broker, settings, ai)
    svc = Services(settings, db, broker, ai, matching)

    async def purge_once() -> None:
        try:
            removed = await purge_expired_rooms(db, settings.room_retention_days)
            if removed:
                log.info("purged %s expired rooms", removed)
        except Exception:
            log.exception("purge failed")

    async def purge_loop() -> None:
        # 대기 중에만 취소되도록 먼저 잠든다. 시작 시 정리는 lifespan에서 끝낸다.
        while True:
            await asyncio.sleep(6 * 3600)
            await purge_once()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await db.create_all()
        await purge_once()
        if not settings.ai_enabled:
            log.warning("ANTHROPIC_API_KEY가 없어 키워드 기반 추천만 사용합니다. 명함 읽기는 꺼집니다.")
        purge = asyncio.create_task(purge_loop())
        try:
            yield
        finally:
            purge.cancel()
            with suppress(asyncio.CancelledError):
                await purge
            await matching.wait_idle()
            await db.dispose()

    app = FastAPI(title="Meetpoint", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = svc
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.include_router(pages.router)
    app.include_router(host.router)
    app.include_router(api.router)

    @app.get("/health", include_in_schema=False)
    async def health() -> JSONResponse:
        return JSONResponse({"ok": True, "ai": settings.ai_enabled})

    return app
