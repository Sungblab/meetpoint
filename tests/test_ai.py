import asyncio
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.matching.ai import FALLBACK_BETA, AIClient, AIUnavailable, parse_recommendations
from app.matching.schemas import CardOut, PairResult, Profile

from .conftest import create_room, join, new_client, state
from .test_flow import DEV, MARKETER


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def _response(text: str | None, stop_reason: str = "end_turn"):
    content = [] if text is None else [SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def _client(model="claude-opus-5", response=None, **overrides) -> tuple[AIClient, FakeMessages]:
    settings = Settings(_env_file=None, anthropic_api_key="test", ai_model=model, **overrides)
    ai = AIClient(settings)
    fake = FakeMessages(response=response)
    ai.client = SimpleNamespace(beta=SimpleNamespace(messages=fake))
    return ai, fake


P1 = Profile(1, "가", "", "개발자", "서버", "마케팅")
P2 = Profile(2, "나", "", "마케터", "", "개발")

GOOD = """{"results":[{"candidate_id":2,
  "for_new":{"kind":"complement","score":88,"reason":"광고 경험이 있어요","opener":"안녕하세요"},
  "for_candidate":{"kind":"complement","score":140,"reason":"개발 비용을 물어보세요","opener":"반가워요"}}]}"""


def test_request_uses_structured_output_effort_and_fallbacks():
    ai, fake = _client(response=_response(GOOD))
    out = asyncio.run(ai.recommend(P1, [P2]))
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["output_config"]["effort"] == "low"
    assert call["fallbacks"] == "default"
    assert call["betas"] == [FALLBACK_BETA]
    assert "thinking" not in call
    forward, backward = out[2]
    assert forward == PairResult("complement", 88, "광고 경험이 있어요", "안녕하세요", "ai")
    assert backward.score == 100  # 범위를 넘으면 잘라낸다


def test_haiku_skips_effort_and_fallbacks():
    ai, fake = _client(model="claude-haiku-4-5", response=_response(GOOD))
    asyncio.run(ai.recommend(P1, [P2]))
    call = fake.calls[0]
    assert "effort" not in call["output_config"]
    assert "fallbacks" not in call and "betas" not in call


def test_fallbacks_can_be_turned_off():
    ai, fake = _client(response=_response(GOOD), ai_fallbacks=False)
    asyncio.run(ai.recommend(P1, [P2]))
    assert "fallbacks" not in fake.calls[0]


@pytest.mark.parametrize(
    "response",
    [
        _response(None, stop_reason="refusal"),
        _response('{"results": [', stop_reason="max_tokens"),
        _response("not json"),
        _response('{"wrong": 1}'),
        _response(None),
    ],
)
def test_bad_responses_raise_unavailable(response):
    ai, _ = _client(response=response)
    with pytest.raises(AIUnavailable):
        asyncio.run(ai.recommend(P1, [P2]))


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


def test_card_request_sends_image_with_low_effort():
    card = '{"is_business_card":true,"name":"홍길동","headline":"회사 · 대표","about":"회사 대표예요","contact":"a@b.c"}'
    ai, fake = _client(response=_response(card))
    out = asyncio.run(ai.read_card(b"\xff\xd8\xffdata", "image/jpeg"))
    assert out.name == "홍길동"
    call = fake.calls[0]
    assert call["output_config"]["effort"] == "low"
    block = call["messages"][0]["content"][0]
    assert block["type"] == "image" and block["source"]["media_type"] == "image/jpeg"


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
        return CardOut(is_business_card=True, name="홍길동", headline="회사 · 대표", about="소개", contact="a@b.c")


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


def test_card_endpoint(app):
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        jpeg = b"\xff\xd8\xff" + b"0" * 100
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 503  # AI 키가 없으면 꺼져 있다

        _with_ai(app, FakeAI())
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 200
        assert res.json() == {"name": "홍길동", "headline": "회사 · 대표", "about": "소개", "contact": "a@b.c"}

        res = a.post(f"/r/{code}/card", files={"file": ("x.txt", b"hello world", "image/jpeg")})
        assert res.status_code == 415

        app.state.services.settings.max_card_bytes = 10
        res = a.post(f"/r/{code}/card", files={"file": ("c.jpg", jpeg, "image/jpeg")})
        assert res.status_code == 413


def test_card_not_a_card(app):
    class NotCard(FakeAI):
        async def read_card(self, image, media_type):
            return CardOut(is_business_card=False, name="", headline="", about="", contact="")

    _with_ai(app, NotCard())
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        res = a.post(f"/r/{code}/card", files={"file": ("c.png", b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")})
        assert res.status_code == 422
