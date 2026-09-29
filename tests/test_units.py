import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.broker import Broker
from app.config import Settings
from app.db import Database
from app.matching.heuristic import score_pair
from app.matching.schemas import Profile
from app.matching.service import purge_expired_rooms
from app.models import Participant, Room
from app.ratelimit import RateLimiter
from app.vcard import build_vcard


def test_heuristic_handles_korean_particles():
    dev = Profile(1, "김개발", "개발자", "쇼핑몰을 만들어요", "", "마케팅을 도와줄 사람")
    marketer = Profile(2, "박마케터", "퍼포먼스 마케터", "마케팅 5년 했어요", "", "")
    r = score_pair(dev, marketer)
    assert r.kind == "complement"
    assert "‘마케팅’" in r.reason
    assert r.score > 30


def test_heuristic_common_field():
    a = Profile(1, "가", "백엔드 개발자", "파이썬 서버 개발", "서버 배포 자동화가 궁금해요", "")
    b = Profile(2, "나", "데브옵스", "서버 배포 자동화를 맡고 있어요", "", "")
    assert score_pair(a, b).kind == "common"


def test_heuristic_no_overlap_is_none():
    a = Profile(1, "가", "", "요리", "레시피", "")
    b = Profile(2, "나", "", "등산", "", "")
    r = score_pair(a, b)
    assert r.kind == "none" and r.reason == "" and r.score <= 20


def test_broker_targets_participant():
    async def run():
        broker = Broker()
        a = broker.subscribe(1, 10)
        b = broker.subscribe(1, 11)
        host = broker.subscribe(1, None)
        other_room = broker.subscribe(2, 10)
        broker.publish(1, "match", {"x": 1}, to=10)
        broker.publish(1, "refresh")
        assert a.queue.qsize() == 2
        assert b.queue.qsize() == 1
        assert host.queue.qsize() == 1
        assert other_room.queue.qsize() == 0
        broker.unsubscribe(a)
        broker.unsubscribe(b)
        broker.unsubscribe(host)
        assert broker.subscriber_count(1) == 0

    asyncio.run(run())


def test_broker_drops_when_queue_full():
    async def run():
        broker = Broker()
        sub = broker.subscribe(1, 1)
        for _ in range(150):
            broker.publish(1, "refresh")
        assert sub.queue.qsize() == 100

    asyncio.run(run())


def test_rate_limiter():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("ip") and limiter.allow("ip")
    assert not limiter.allow("ip")
    assert limiter.allow("other")


def test_purge_expired_rooms(tmp_path):
    async def run():
        db = Database(f"sqlite+aiosqlite:///{tmp_path / 'p.db'}")
        await db.create_all()
        async with db.sessionmaker() as s:
            old = Room(code="OLD111", host_token_hash="a" * 64, name="old", created_at=datetime.now(UTC) - timedelta(days=40))
            new = Room(code="NEW111", host_token_hash="b" * 64, name="new")
            s.add_all([old, new])
            await s.flush()
            s.add(Participant(room_id=old.id, token_hash="c" * 64, name="x"))
            await s.commit()
        removed = await purge_expired_rooms(db, 30)
        async with db.sessionmaker() as s:
            rooms = (await s.execute(Room.__table__.select())).all()
            people = (await s.execute(Participant.__table__.select())).all()
        await db.dispose()
        return removed, [r.code for r in rooms], people

    removed, codes, people = asyncio.run(run())
    assert removed == 1
    assert codes == ["NEW111"]
    assert people == []


def test_settings_ai_enabled():
    assert not Settings(_env_file=None, gemini_api_key="").ai_enabled
    assert Settings(_env_file=None, gemini_api_key="k").ai_enabled


def test_create_all_adds_new_columns_to_old_table(tmp_path):
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'old.db'}")

    async def run():
        async with db.engine.begin() as conn:
            await conn.execute(text(
                "CREATE TABLE participants (id INTEGER PRIMARY KEY, room_id INTEGER, token_hash VARCHAR(64), "
                "name VARCHAR(30), headline VARCHAR(60), about TEXT, ask_same TEXT, ask_other TEXT, "
                "find_me VARCHAR(60), contact VARCHAR(100), recs_status VARCHAR(10), profile_version INTEGER, "
                "created_at DATETIME, updated_at DATETIME)"
            ))
            await conn.execute(text("INSERT INTO participants (id, room_id, token_hash, name) VALUES (1, 1, 'x', '가')"))
        await db.create_all()
        async with db.engine.connect() as conn:
            row = (await conn.execute(text("SELECT phone, email FROM participants WHERE id = 1"))).one()
        await db.dispose()
        return tuple(row)

    assert asyncio.run(run()) == ("", "")


def test_vcard_escapes_special_characters():
    body = build_vcard(name="김, 하늘;", headline="대표\\CEO", phone="010-1234-5678", email="",
                       other="카톡 abc", note="이유\n둘째 줄")
    assert "FN:김\\, 하늘\\;" in body
    assert "TITLE:대표\\\\CEO" in body
    assert "EMAIL" not in body
    assert "NOTE:이유\\n둘째 줄\\n기타 연락처: 카톡 abc" in body
    assert body.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n")
    assert body.endswith("END:VCARD\r\n")
