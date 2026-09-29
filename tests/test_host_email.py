import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app import mail
from app.db import Database
from app.main import create_app
from app.models import Room

from .conftest import create_room

SENT: list = []


class FakeSMTP:
    def __init__(self, host, port, timeout):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context):
        pass

    def login(self, user, password):
        pass

    def send_message(self, msg):
        SENT.append(msg)


@pytest.fixture
def mail_app(settings, monkeypatch):
    SENT.clear()
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    settings.smtp_host = "smtp.test"
    settings.smtp_user = "meetpoint@example.com"
    settings.public_base_url = "https://meetpoint.test"
    return create_app(settings)


def rooms(app) -> list[Room]:
    async def read():
        async with app.state.services.db.sessionmaker() as s:
            return (await s.scalars(select(Room).order_by(Room.id))).all()

    return asyncio.run(read())


def test_room_needs_host_email(client):
    for email in ("", "not-an-email", "a@b"):
        res = client.post("/rooms", data={"name": "밋업", "email": email})
        assert res.status_code == 400
        assert "이메일" in res.text


def test_room_mails_host_link(mail_app):
    with TestClient(mail_app) as c:
        token, code = create_room(c, name="AI 서비스 밋업", email=" Host@Example.com ")
        assert "host@example.com로도 보냈어요" in c.get(f"/h/{token}").text
    [msg] = SENT
    assert msg["To"] == "host@example.com"
    assert "AI 서비스 밋업" in msg["Subject"]
    body = msg.get_content()
    assert f"https://meetpoint.test/h/{token}" in body
    assert f"https://meetpoint.test/r/{code}" in body


def test_marketing_consent_is_opt_in(client, app):
    create_room(client, name="동의 안 함")
    create_room(client, name="동의함", marketing="1")
    no, yes = rooms(app)
    assert no.host_email == "host@example.com" and no.marketing_consent_at == ""
    assert yes.marketing_consent_at != ""


def test_create_all_adds_host_columns_to_old_rooms(tmp_path):
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'old.db'}")

    async def run():
        async with db.engine.begin() as conn:
            await conn.execute(text(
                "CREATE TABLE rooms (id INTEGER PRIMARY KEY, code VARCHAR(12), host_token_hash VARCHAR(64), "
                "name VARCHAR(80), description VARCHAR(300), created_at DATETIME, closed_at DATETIME)"
            ))
            await conn.execute(text("INSERT INTO rooms (id, code, host_token_hash, name) VALUES (1, 'OLD111', 'x', '옛 방')"))
        await db.create_all()
        async with db.engine.connect() as conn:
            row = (await conn.execute(text("SELECT host_email, marketing_consent_at FROM rooms WHERE id = 1"))).one()
        await db.dispose()
        return tuple(row)

    assert asyncio.run(run()) == ("", "")
