import pytest
from fastapi.testclient import TestClient

from app.main import create_app

from .conftest import create_room, join, new_client, state
from .test_flow import DEV, MARKETER

AUTH = ("admin", "long-test-password")


@pytest.fixture
def admin_app(settings):
    settings.admin_password = AUTH[1]
    return create_app(settings)


def test_admin_is_off_without_password(client):
    assert client.get("/admin", auth=AUTH).status_code == 404


def test_admin_needs_password(admin_app):
    with TestClient(admin_app) as c:
        res = c.get("/admin")
        assert res.status_code == 401
        assert res.headers["www-authenticate"].startswith("Basic")
        assert c.get("/admin", auth=("admin", "wrong")).status_code == 401
        assert c.get("/admin/r/ZZZZZZ", auth=("admin", "wrong")).status_code == 401


def test_admin_blocks_repeated_wrong_passwords(admin_app):
    with TestClient(admin_app) as c:
        for _ in range(3):
            assert c.get("/admin").status_code == 401  # 비밀번호를 묻는 첫 요청은 세지 않는다
        for _ in range(10):
            assert c.get("/admin", auth=("admin", "wrong")).status_code == 401
        assert c.get("/admin", auth=("admin", "wrong")).status_code == 429
        # 한도에 닿으면 맞는 비밀번호도 잠시 받지 않는다.
        assert c.get("/admin", auth=AUTH).status_code == 429


def test_admin_shows_rooms_and_people_without_contacts(admin_app):
    with TestClient(admin_app) as host, new_client(admin_app) as a, new_client(admin_app) as b:
        _, code = create_room(host, name="AI 서비스 밋업")
        join(a, code, **dict(DEV, phone="010-1234-5678", email="dev-card@example.com"))
        join(b, code, **MARKETER)
        a_id, b_id = state(a, code)["me"]["id"], state(b, code)["me"]["id"]
        a.post(f"/r/{code}/api/like/{b_id}", json={"liked": True})
        b.post(f"/r/{code}/api/like/{a_id}", json={"liked": True})

        home = host.get("/admin", auth=AUTH)
        assert home.status_code == 200
        assert "AI 서비스 밋업" in home.text
        assert "host@example.com" in home.text
        assert f"/admin/r/{code}" in home.text
        assert "김개발" in home.text and "박마케터" in home.text

        page = host.get(f"/admin/r/{code}", auth=AUTH)
        assert page.status_code == 200
        assert DEV["about"] in page.text and MARKETER["ask_other"] in page.text
        for text in (home.text, page.text):
            for secret in (DEV["contact"], MARKETER["contact"], "010-1234-5678", "dev-card@example.com"):
                assert secret not in text

        assert host.get("/admin/r/ZZZZZZ", auth=AUTH).status_code == 404
