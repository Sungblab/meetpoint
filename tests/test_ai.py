import asyncio
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors, types

from app.broker import Broker
from app.config import Settings
from app.main import create_app
from app.matching import service
from app.matching.ai import AIClient, AIUnavailable, parse_recommendations
from app.matching.schemas import RECOMMENDATION_SCHEMA, CardOut, PairResult, Profile

from .conftest import create_room, join, new_client, state
from .test_flow import DEV, MARKETER


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def _response(text: str | None, finish_reason: str = "STOP"):
    parts = [] if text is None else [types.Part(text=text)]
    candidate = types.Candidate(content=types.Content(role="model", parts=parts), finish_reason=finish_reason)
    return types.GenerateContentResponse(candidates=[candidate])


def _client(response=None, error=None, **overrides) -> tuple[AIClient, FakeModels]:
    settings = Settings(_env_file=None, gemini_api_key="test", **overrides)
    ai = AIClient(settings)
    fake = FakeModels(response=response, error=error)
    ai.client = SimpleNamespace(models=fake)
    return ai, fake


P1 = Profile(1, "가", "", "개발자", "서버", "마케팅")
P2 = Profile(2, "나", "", "마케터", "", "개발")

GOOD = """{"results":[{"candidate_id":2,
  "for_new":{"kind":"complement","score":88,"reason":"광고 경험이 있어요","opener":"안녕하세요"},
  "for_candidate":{"kind":"complement","score":140,"reason":"개발 비용을 물어보세요","opener":"반가워요"}}]}"""


def test_request_uses_json_schema_and_low_thinking():
    ai, fake = _client(response=_response(GOOD))
    out = asyncio.run(ai.recommend(P1, [P2]))
    call = fake.calls[0]
    config = call["config"]
    assert call["model"] == "gemini-3.8-flash"
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == RECOMMENDATION_SCHEMA
    assert config.thinking_config.thinking_level == types.ThinkingLevel.LOW
    forward, backward = out[2]
    assert forward == PairResult("complement", 88, "광고 경험이 있어요", "안녕하세요", "ai")
    assert backward.score == 100  # 범위를 넘으면 잘라낸다


def test_empty_effort_leaves_thinking_to_model():
    ai, fake = _client(response=_response(GOOD), ai_effort="")
    asyncio.run(ai.recommend(P1, [P2]))
    assert fake.calls[0]["config"].thinking_config is None


@pytest.mark.parametrize(
    "response",
    [
        _response(None, finish_reason="SAFETY"),
        _response('{"results": [', finish_reason="MAX_TOKENS"),
        _response("not json"),
        _response('{"wrong": 1}'),
        _response(None),
        types.GenerateContentResponse(
            candidates=[],
            prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason="PROHIBITED_CONTENT"),
        ),
    ],
)
def test_bad_responses_raise_unavailable(response):
    ai, _ = _client(response=response)
    with pytest.raises(AIUnavailable):
        asyncio.run(ai.recommend(P1, [P2]))


@pytest.mark.parametrize(
    "error",
    [errors.ServerError(503, {"error": {"message": "overloaded"}}), httpx.ConnectTimeout("slow")],
)
def test_api_errors_raise_unavailable(error):
    ai, _ = _client(error=error)
    with pytest.raises(AIUnavailable):
        asyncio.run(ai.recommend(P1, [P2]))


def test_daily_limit_covers_recommendations_and_cards():
    ai, fake = _client(response=_response(GOOD), ai_daily_limit=1)
    asyncio.run(ai.recommend(P1, [P2]))
    with pytest.raises(AIUnavailable):
        asyncio.run(ai.read_card(b"\xff\xd8\xffdata", "image/jpeg"))
    assert len(fake.calls) == 1


def test_parse_drops_unknown_and_duplicate_ids_and_blanks_none():
    data = {
        "results": [
            {"candidate_id": 9, "for_new": {"kind": "common", "score": 50, "reason": "x", "opener": "y"},
             "for_candidate": {"kind": "common", "score": 50, "reason": "x", "opener": "y"}},
            {"candidate_id": 2, "for_new": {"kind": "none", "score": 70, "reason": "지어낸 이유", "opener": "말"},
             "for_candidate": {"kind": "common", "score": -5, "reason": "r", "opener": "o"}},
            {"candidate_id": 2, "for_new": {"kind": "common", "score": 99, "reason": "dup", "opener": "dup"},
             "for_candidate": {"kind": "common", "score": 99, "reason": "dup", "opener": "dup"}},
        ]
    }
    out = parse_recommendations(data, {2})
    assert set(out) == {2}
    forward, backward = out[2]
    assert forward == PairResult("none", 20, "", "", "ai")
    assert backward.score == 0


def test_reasons_drop_links_and_contacts():
    reason = "https://evil.example/join 에서 가입하고 010-1234-5678이나 a@evil.co.kr, evil.com으로 연락해요"
    data = {"results": [{"candidate_id": 2,
                         "for_new": {"kind": "common", "score": 90, "reason": reason, "opener": "www.evil.kr 보셨어요?"},
                         "for_candidate": {"kind": "common", "score": 90, "reason": "ASP.NET 경험이 2020.03.01부터 있어요", "opener": "안녕하세요"}}]}
    forward, backward = parse_recommendations(data, {2})[2]
    assert forward.reason == "에서 가입하고 이나 , 연락해요"
    assert forward.opener == "보셨어요?"
    # 주소나 전화번호가 아닌 글은 그대로 둔다.
    assert backward.reason == "ASP.NET 경험이 2020.03.01부터 있어요"


def test_card_request_sends_image_with_low_thinking():
    card = ('{"is_business_card":true,"name":"홍길동","company":"회사","job_title":"대표","headline":"","about":"회사 대표예요",'
            '"phone":"010-1234-5678","email":"a@b.c","contact":"https://example.com"}')
    ai, fake = _client(response=_response(card))
    out = asyncio.run(ai.read_card(b"\xff\xd8\xffdata", "image/jpeg"))
    assert out.name == "홍길동"
    assert out.phone == "010-1234-5678" and out.email == "a@b.c"
    assert out.company == "회사" and out.job_title == "대표"
    call = fake.calls[0]
    assert call["config"].thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert "해요체" in call["config"].system_instruction  # 앱의 다른 문장과 말투를 맞춘다
    image = call["contents"][0]
    assert image.inline_data.mime_type == "image/jpeg" and image.inline_data.data == b"\xff\xd8\xffdata"


class FakeAI:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = 0

    async def recommend(self, new, candidates):
        self.calls += 1
        if self.fail:
            raise AIUnavailable("down")
        return {
            c.id: (
                PairResult("common", 77, f"{c.name}님과 AI가 찾은 연결점", "AI 첫마디", "ai"),
                PairResult("complement", 66, f"{new.name}님과 AI가 찾은 연결점", "AI 첫마디", "ai"),
            )
            for c in candidates
        }

    async def read_card(self, image, media_type):
        return CardOut(is_business_card=True, name="홍길동", company="회사", job_title="대표", headline="", about="소개",
                       phone="010-1234-5678", email="a@b.c", contact="https://example.com")


def _with_ai(app, fake):
    svc = app.state.services
    svc.ai = fake
    svc.matching.ai = fake


def test_ai_results_are_stored_and_shown(app):
    fake = FakeAI()
    _with_ai(app, fake)
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        rec_a = state(a, code)["people"][0]["rec"]
        rec_b = state(b, code)["people"][0]["rec"]
    assert fake.calls == 1  # 두 번째 사람이 들어올 때 한 번만 부른다
    assert rec_b == {"kind": "common", "score": 77, "reason": "김개발님과 AI가 찾은 연결점", "opener": "AI 첫마디", "source": "ai"}
    assert rec_a["kind"] == "complement" and rec_a["source"] == "ai"


def test_ai_failure_falls_back_to_keywords(app):
    _with_ai(app, FakeAI(fail=True))
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        s = state(a, code)
    assert s["me"]["recs_status"] == "ready"
    assert s["people"][0]["rec"]["source"] == "heuristic"


def test_large_room_is_evaluated_in_batches(app, settings):
    settings.ai_batch_size = 2
    fake = FakeAI()
    _with_ai(app, fake)
    with new_client(app) as host:
        _, code = create_room(host)
        clients = [new_client(app) for _ in range(5)]
        for i, c in enumerate(clients):
            c.__enter__()
            join(c, code, name=f"사람{i}", about="개발자", ask_same="배포")
        last = state(clients[-1], code)
        for c in clients:
            c.__exit__(None, None, None)
    # 0+1+1+2+2 배치 (들어올 때마다 기존 인원을 2명씩 나눠 평가)
    assert fake.calls == 6
    assert all(p["rec"]["source"] == "ai" for p in last["people"])


def test_room_ai_budget_falls_back_to_keywords(settings):
    settings.ai_room_daily_limit = 1
    app = create_app(settings)
    fake = FakeAI()
    _with_ai(app, fake)
    with new_client(app) as host, new_client(app) as a, new_client(app) as b, new_client(app) as c:
        _, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        join(c, code, name="셋째", about="쇼핑몰 개발자", ask_same="배포")
        people = state(c, code)["people"]
    assert fake.calls == 1
    assert {p["rec"]["source"] for p in people} == {"heuristic"}


def test_matching_runs_one_job_per_participant(monkeypatch):
    async def run():
        matching = service.MatchingService(None, Broker(), Settings(_env_file=None), None)
        calls = []
        gate = asyncio.Event()

        async def fake_run(room_id, participant_id, use_ai=True):
            calls.append((participant_id, use_ai))
            await gate.wait()

        matching.run = fake_run
        await matching.enqueue(1, 10)
        await asyncio.sleep(0)
        for _ in range(5):
            await matching.enqueue(1, 10)
        monkeypatch.setattr(service, "MAX_JOBS", 1)
        await matching.enqueue(1, 11)
        gate.set()
        await matching.wait_idle()
        return calls

    calls = asyncio.run(run())
    # 도는 중에 다섯 번 더 불러도 끝난 뒤 한 번만 다시 돈다. 작업이 많으면 새 작업은 AI를 쓰지 않는다.
    assert sorted(calls) == [(10, True), (10, True), (11, False)]


def test_card_endpoint(app):
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        jpeg = b"\xff\xd8\xff" + b"0" * 100
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 503  # AI 키가 없으면 꺼져 있다

        _with_ai(app, FakeAI())
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 200
        assert res.json() == {"name": "홍길동", "company": "회사", "job_title": "대표", "headline": "", "about": "소개",
                              "phone": "010-1234-5678", "email": "a@b.c", "contact": "https://example.com"}

        res = a.post(f"/r/{code}/card", files={"file": ("x.txt", b"hello world", "image/jpeg")})
        assert res.status_code == 415

        app.state.services.settings.max_card_bytes = 10
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 413


def test_card_not_a_card(app):
    class NotCard(FakeAI):
        async def read_card(self, image, media_type):
            return CardOut(is_business_card=False, name="", company="", job_title="", headline="", about="", phone="", email="", contact="")

    _with_ai(app, NotCard())
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        res = a.post(f"/r/{code}/card", files={"file": ("c.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")})
        assert res.status_code == 422
