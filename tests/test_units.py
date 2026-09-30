import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.broker import Broker
from app.config import Settings
from app.db import Database
from app.matching.heuristic import score_pair
from app.matching.schemas import Profile
from app.matching.service import purge_legacy_rooms
from app.models import Participant, Room
from app.ratelimit import RateLimiter
from app.routes.api import sse_response
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


def test_broker_closes_oldest_stream_over_limits():
    async def run():
        broker = Broker(per_client=3, total=5)
        a = [broker.subscribe(1, 10) for _ in range(4)]
        # 한 사람이 네 번째 연결을 열면 가장 오래된 연결이 닫힌다.
        assert a[0].queue.get_nowait() == ("closed", {})
        broker.publish(1, "refresh", to=10)
        assert [s.queue.qsize() for s in a] == [0, 1, 1, 1]
        hosts = [broker.subscribe(1, None) for _ in range(4)]
        assert hosts[0].queue.get_nowait() == ("closed", {})
        # 전체 한도를 넘으면 참가자와 상관없이 가장 오래된 연결부터 닫는다.
        # 닫을 때는 쌓인 알림을 비우고 closed만 남긴다.
        assert list(a[1].queue._queue) == [("closed", {})]
        broker.subscribe(2, 20)
        assert list(a[2].queue._queue) == [("closed", {})]
        assert broker.subscriber_count(1) == 4 and broker.subscriber_count(2) == 1

    asyncio.run(run())


def test_sse_stream_ends_when_broker_closes_it():
    class Connected:
        async def is_disconnected(self):
            return False

    async def run():
        broker = Broker(per_client=1)
        res = sse_response(Connected(), broker, 1, 10)
        broker.subscribe(1, 10)  # 같은 사람의 새 연결이 먼저 연 연결을 닫는다
        return [chunk async for chunk in res.body_iterator]

    chunks = asyncio.run(run())
    assert chunks[-1] == "event: closed\ndata: {}\n\n"


def test_rate_limiter():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("ip") and limiter.allow("ip")
    assert not limiter.allow("ip")
    assert limiter.allow("other")
    # blocked는 세지 않고 확인만 한다.
    misses = RateLimiter(limit=2, window_seconds=60)
    assert not misses.blocked("ip") and not misses.blocked("ip")
    misses.allow("ip")
    misses.allow("ip")
    assert misses.blocked("ip")


def test_purge_only_legacy_rooms(tmp_path):
    now = datetime.now(UTC)

    async def run():
        db = Database(f"sqlite+aiosqlite:///{tmp_path / 'p.db'}")
        await db.create_all()
        async with db.sessionmaker() as s:
            legacy = Room(code="OLD111", host_token_hash="a" * 64, name="old", created_at=now - timedelta(days=40))
            kept = Room(code="KEEP11", host_token_hash="b" * 64, name="kept", created_at=now - timedelta(days=32))
            new = Room(code="NEW111", host_token_hash="c" * 64, name="new")
            s.add_all([legacy, kept, new])
            await s.flush()
            s.add(Participant(room_id=legacy.id, token_hash="d" * 64, name="x"))
            await s.commit()
        # 35일 전부터는 "지우지 않는다"는 안내로 만든 방이라고 친다.
        removed = await purge_legacy_rooms(db, legacy_before=now - timedelta(days=35))
        async with db.sessionmaker() as s:
            rooms = (await s.execute(Room.__table__.select())).all()
            people = (await s.execute(Participant.__table__.select())).all()
        await db.dispose()
        return removed, {r.code for r in rooms}, people

    removed, codes, people = asyncio.run(run())
    assert removed == 1
    assert codes == {"KEEP11", "NEW111"}
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
    body = build_vcard(name="김, 하늘;", company="", job_title="", headline="대표\\CEO", phone="010-1234-5678", email="",
                       other="카톡 abc", note="이유\n둘째 줄")
    assert "FN:김\\, 하늘\\;" in body
    assert "TITLE:대표\\\\CEO" in body
    assert "EMAIL" not in body
    assert "NOTE:이유\\n둘째 줄\\n기타 연락처: 카톡 abc" in body
    assert body.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n")
    assert body.endswith("END:VCARD\r\n")
    # 홀로 쓴 CR로 URL 같은 칸을 끼워 넣지 못한다.
    body = build_vcard(name="가", company="", job_title="", headline="", phone="", email="", other="",
                       note="이유\rURL:https://evil.example")
    assert "NOTE:이유\\nURL:https://evil.example\r\n" in body
    assert "\rURL" not in body


def test_vcard_puts_company_and_title_in_their_own_fields():
    body = build_vcard(name="박준영", headline="밀키트 구독 2년째", company="밀키트컴퍼니", job_title="대표",
                       phone="", email="", other="", note="")
    assert "ORG:밀키트컴퍼니\r\n" in body
    assert "TITLE:대표\r\n" in body


def test_profile_sends_company_and_title_to_ai():
    d = Profile(1, "가", "", "소개", "", "", company="밀키트컴퍼니", job_title="대표").as_prompt_dict()
    assert d["company"] == "밀키트컴퍼니" and d["job_title"] == "대표"


def test_heuristic_reads_job_title():
    viewer = Profile(1, "가", "", "반찬 구독을 준비해요", "", "세무사 상담이 필요해요")
    target = Profile(2, "나", "", "초기 스타트업을 도와요", "", "", job_title="세무사")
    assert score_pair(viewer, target).kind == "complement"
