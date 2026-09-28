import asyncio
import os
import re

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import Base, Database
from app.main import create_app

# 예: TEST_DATABASE_URL=postgresql+asyncpg://meetpoint@127.0.0.1:55432/meetpoint_test
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")


async def _reset_schema(url: str) -> None:
    from app import models  # noqa: F401

    db = Database(url, pool=False)
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await db.dispose()


@pytest.fixture
def settings(tmp_path) -> Settings:
    url = TEST_DATABASE_URL or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    if TEST_DATABASE_URL:
        asyncio.run(_reset_schema(url))
    return Settings(
        _env_file=None,
        database_url=url,
        database_pool=False,
        anthropic_api_key="",
        inline_tasks=True,
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def new_client(app) -> TestClient:
    return TestClient(app)


def create_room(client: TestClient, name: str = "자사몰 특강") -> tuple[str, str]:
    """(host_token, room_code)"""
    res = client.post("/rooms", data={"name": name}, follow_redirects=False)
    assert res.status_code == 303, res.text
    token = res.headers["location"].rsplit("/", 1)[-1]
    page = client.get(f"/h/{token}")
    code = re.search(r"참가 코드 <strong>([A-Z0-9]+)</strong>", page.text).group(1)
    return token, code


def join(client: TestClient, code: str, **fields) -> None:
    data = {
        "name": "참가자",
        "about": "소개",
        "ask_same": "",
        "ask_other": "",
        "headline": "",
        "find_me": "",
        "contact": "",
    }
    data.update(fields)
    res = client.post(f"/r/{code}/join", data=data, follow_redirects=False)
    assert res.status_code == 303, res.text


def state(client: TestClient, code: str) -> dict:
    res = client.get(f"/r/{code}/api/state")
    assert res.status_code == 200, res.text
    return res.json()
