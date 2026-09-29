from sqlalchemy import func, select

from app.models import Like, Participant, Recommendation

from .conftest import create_room, join, new_client, state

DEV = dict(
    name="김개발",
    headline="자사몰 창업 준비 · 백엔드 개발자",
    about="자사몰을 직접 개발하고 있어요. 서버와 배포는 해봤어요.",
    ask_same="카페24로 할지 자체 개발로 할지 고민이에요",
    ask_other="마케팅이 걱정이라 광고 마케터와 이야기하고 싶어요",
    find_me="파란 셔츠, 3번 테이블",
    contact="dev@example.com",
)
MARKETER = dict(
    name="박마케터",
    headline="퍼포먼스 마케터",
    about="쇼핑몰 광고와 SNS 마케팅을 5년 했어요.",
    ask_same="",
    ask_other="자체 개발 쇼핑몰의 개발 비용이 궁금해요",
    find_me="창가 쪽",
    contact="marketer@example.com",
)


def test_landing_and_create_room(client):
    assert client.get("/").status_code == 200
    token, code = create_room(client)
    assert len(code) == 6
    page = client.get(f"/h/{token}")
    assert "<svg" in page.text
    assert f"/r/{code}" in page.text
    stats = client.get(f"/h/{token}/api/stats").json()
    assert stats == {"closed": False, "participants": 0, "pending": 0, "matches": 0, "people": []}


def test_create_room_requires_name(client):
    res = client.post("/rooms", data={"name": "  "})
    assert res.status_code == 400
    assert "행사 이름" in res.text


def test_unknown_room_and_host_token(client):
    assert client.get("/r/ZZZZZZ").status_code == 404
    assert client.get("/h/not-a-token").status_code == 404


def test_lowercase_code_redirects(client):
    _, code = create_room(client)
    res = client.get(f"/r/{code.lower()}", follow_redirects=False)
    assert res.status_code == 307
    assert res.headers["location"] == f"/r/{code}"


def test_join_validation(client):
    _, code = create_room(client)
    res = client.post(f"/r/{code}/join", data={"name": "", "about": "", "ask_same": "", "ask_other": ""})
    assert res.status_code == 400
    assert "이름을 적어주세요" in res.text
    assert "하나는 적어주세요" in res.text
    res = client.post(f"/r/{code}/join", data={"name": "가" * 31, "about": "x", "ask_same": "y"})
    assert res.status_code == 400
    assert "30자" in res.text


def test_two_people_get_recommendations_both_ways(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)

        sa = state(a, code)
        assert sa["me"]["recs_status"] == "ready"
        assert [p["name"] for p in sa["people"]] == ["박마케터"]
        rec = sa["people"][0]["rec"]
        assert rec["kind"] == "complement"
        assert "마케팅" in rec["reason"]
        assert rec["opener"]

        sb = state(b, code)
        rec_b = sb["people"][0]["rec"]
        assert rec_b is not None
        assert rec_b["kind"] == "complement"
        # 찾는 법은 모두에게, 연락처는 연결된 사람에게만 보인다.
        assert sb["people"][0]["find_me"] == "파란 셔츠, 3번 테이블"
        assert sb["people"][0]["contact"] is None


def test_mutual_like_reveals_contact(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        token, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        b_id = state(a, code)["people"][0]["id"]
        a_id = state(b, code)["people"][0]["id"]

        res = a.post(f"/r/{code}/api/like/{b_id}", json={"liked": True}).json()
        assert res == {"liked": True, "matched": False, "name": "박마케터", "contact": None, "phone": None, "email": None}
        # 한쪽만 누르면 상대 화면에는 아무 표시도 없다.
        other = state(b, code)["people"][0]
        assert other["liked"] is False and other["matched"] is False and other["contact"] is None

        res = b.post(f"/r/{code}/api/like/{a_id}", json={"liked": True}).json()
        assert res["matched"] is True
        assert res["contact"] == "dev@example.com"

        pa = state(a, code)["people"][0]
        assert pa["matched"] is True and pa["contact"] == "marketer@example.com"
        assert state(a, code)["counts"]["matches"] == 1
        assert host.get(f"/h/{token}/api/stats").json()["matches"] == 1

        # 취소하면 연락처가 다시 가려진다.
        res = a.post(f"/r/{code}/api/like/{b_id}", json={"liked": False}).json()
        assert res["matched"] is False
        assert state(b, code)["people"][0]["contact"] is None


def test_like_is_idempotent_and_scoped_to_room(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b, new_client(app) as c:
        _, code1 = create_room(host, "방1")
        _, code2 = create_room(host, "방2")
        join(a, code1, **DEV)
        join(b, code1, **MARKETER)
        join(c, code2, name="다른방", about="다른 방 사람", ask_same="아무거나")
        b_id = state(a, code1)["people"][0]["id"]
        c_id = state(c, code2)["me"]["id"]
        a_id = state(a, code1)["me"]["id"]

        a.post(f"/r/{code1}/api/like/{b_id}", json={"liked": True})
        a.post(f"/r/{code1}/api/like/{b_id}", json={"liked": True})
        assert a.post(f"/r/{code1}/api/like/{c_id}", json={"liked": True}).status_code == 404
        assert a.post(f"/r/{code1}/api/like/{a_id}", json={"liked": True}).status_code == 404

    async def count_likes():
        async with app.state.services.db.sessionmaker() as s:
            return await s.scalar(select(func.count()).select_from(Like))

    import asyncio

    assert asyncio.run(count_likes()) == 1


def test_participant_cookie_is_per_room(app):
    with new_client(app) as host, new_client(app) as a:
        _, code1 = create_room(host, "방1")
        _, code2 = create_room(host, "방2")
        join(a, code1, **DEV)
        assert a.get(f"/r/{code1}/api/state").status_code == 200
        assert a.get(f"/r/{code2}/api/state").status_code == 401
        assert a.get(f"/r/{code2}/api/events").status_code == 401
        # 두 번째 방에서는 입장 화면이 나온다.
        assert "2분만 적어주세요" in a.get(f"/r/{code2}").text


def test_anonymous_cannot_read_state(client):
    _, code = create_room(client)
    assert client.get(f"/r/{code}/api/state").status_code == 401
    assert client.post(f"/r/{code}/api/like/1", json={"liked": True}).status_code == 401


def test_closed_room_blocks_new_joins(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        token, code = create_room(host)
        join(a, code, **DEV)
        host.post(f"/h/{token}/close")
        assert "마감" in b.get(f"/r/{code}").text
        res = b.post(f"/r/{code}/join", data={"name": "늦은사람", "about": "x", "ask_same": "y"})
        assert res.status_code == 400
        # 이미 들어온 사람은 계속 쓴다.
        assert state(a, code)["room"]["closed"] is True
        host.post(f"/h/{token}/reopen")
        join(b, code, **MARKETER)


def test_max_participants(app, settings):
    settings.max_participants = 1
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **DEV)
        res = b.post(f"/r/{code}/join", data={"name": "b", "about": "x", "ask_same": "y"})
        assert res.status_code == 400
        assert "정원" in res.text


def test_edit_profile_recomputes(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        assert state(a, code)["people"][0]["rec"]["kind"] == "complement"

        edited = dict(DEV, ask_other="", ask_same="백엔드 서버 배포 경험을 듣고 싶어요")
        res = a.post(f"/r/{code}/me", data=edited, follow_redirects=False)
        assert res.status_code == 303
        page = a.get(f"/r/{code}/me")
        assert "백엔드 서버 배포" in page.text
        rec = state(a, code)["people"][0]["rec"]
        assert rec["kind"] != "complement"

    async def version():
        async with app.state.services.db.sessionmaker() as s:
            return await s.scalar(select(Participant.profile_version).where(Participant.name == "김개발"))

    import asyncio

    assert asyncio.run(version()) == 2


def test_contact_only_edit_keeps_version(app):
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        join(a, code, **DEV)
        a.post(f"/r/{code}/me", data=dict(DEV, contact="new@example.com"))

    async def version():
        async with app.state.services.db.sessionmaker() as s:
            return await s.scalar(select(Participant.profile_version))

    import asyncio

    assert asyncio.run(version()) == 1


def test_leave_deletes_my_data(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        token, code = create_room(host)
        join(a, code, **DEV)
        join(b, code, **MARKETER)
        b_id = state(a, code)["people"][0]["id"]
        a.post(f"/r/{code}/api/like/{b_id}", json={"liked": True})

        res = a.post(f"/r/{code}/leave", follow_redirects=False)
        assert res.status_code == 303
        assert a.get(f"/r/{code}/api/state").status_code == 401
        assert state(b, code)["people"] == []
        assert host.get(f"/h/{token}/api/stats").json()["participants"] == 1

    async def counts():
        async with app.state.services.db.sessionmaker() as s:
            likes = await s.scalar(select(func.count()).select_from(Like))
            recs = await s.scalar(select(func.count()).select_from(Recommendation))
            return likes, recs

    import asyncio

    assert asyncio.run(counts()) == (0, 0)


def test_host_delete_room(app):
    with new_client(app) as host, new_client(app) as a:
        token, code = create_room(host)
        join(a, code, **DEV)
        res = host.post(f"/h/{token}/delete")
        assert res.status_code == 200
        assert host.get(f"/h/{token}").status_code == 404
        assert a.get(f"/r/{code}").status_code == 404


def test_screen_is_public_and_hides_host_token(app):
    with new_client(app) as host, new_client(app) as viewer:
        token, code = create_room(host)
        page = viewer.get(f"/s/{code}")
        assert page.status_code == 200
        assert token not in page.text
        assert viewer.get(f"/s/{code}/count").json() == {"count": 0, "closed": False}


def test_html_escapes_user_input(app):
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host, "<script>alert(1)</script>")
        page = a.get(f"/r/{code}")
        assert "<script>alert(1)</script>" not in page.text
        assert "&lt;script&gt;" in page.text


def test_many_joins_from_one_venue_wifi(app):
    """행사장에서는 모두 같은 공인 IP로 들어온다. 입장이 IP 제한에 걸리면 안 된다."""
    with new_client(app) as host:
        _, code = create_room(host)
        for i in range(40):
            with new_client(app) as c:
                join(c, code, name=f"참가자{i}", about="쇼핑몰 개발", ask_same="배포")
        assert host.get(f"/s/{code}/count").json()["count"] == 40



def test_legal_pages(client):
    assert "개인정보 보호책임자" in client.get("/privacy").text
    assert "금지 행위" in client.get("/terms").text
    assert 'href="/privacy"' in client.get("/").text
    privacy = client.get("/privacy").text
    assert "전화번호, 이메일, 기타 연락처" in privacy
    assert "휴대폰 연락처에 저장할 수 있습니다" in privacy


def test_join_validates_phone_and_email(client):
    _, code = create_room(client)
    res = client.post(f"/r/{code}/join", data=dict(DEV, phone="전화해", email="dev-at-example"), follow_redirects=False)
    assert res.status_code == 400
    assert "전화번호는" in res.text
    assert "이메일 주소를" in res.text


def test_join_accepts_common_phone_formats(app):
    phones = ["010-1234-5678", "010 1234 5678", "+82 10-1234-5678", "02-123-4567", "(02) 123-4567", "010.1234.5678"]
    for i, phone in enumerate(phones):
        with new_client(app) as c:
            _, code = create_room(c, name=f"방 {i}")
            join(c, code, **dict(DEV, phone=phone, email="Dev@Example.com"))


def test_phone_only_edit_keeps_version(app):
    with new_client(app) as host, new_client(app) as a:
        _, code = create_room(host)
        join(a, code, **DEV)
        a.post(f"/r/{code}/me", data=dict(DEV, phone="010-9999-0000", email="new@example.com"))

    async def read():
        async with app.state.services.db.sessionmaker() as s:
            p = await s.scalar(select(Participant))
            return p.profile_version, p.phone, p.email

    import asyncio

    assert asyncio.run(read()) == (1, "010-9999-0000", "new@example.com")


def test_vcard_only_for_mutual_connections(app):
    with new_client(app) as host, new_client(app) as a, new_client(app) as b:
        _, code = create_room(host)
        join(a, code, **dict(DEV, phone="010-1111-2222", email="dev@example.com"))
        join(b, code, **dict(MARKETER, phone="010-3333-4444", email="mk@example.com"))
        b_id = state(a, code)["people"][0]["id"]
        a_id = state(b, code)["people"][0]["id"]

        assert state(a, code)["people"][0]["phone"] is None
        assert a.get(f"/r/{code}/api/vcard/{b_id}").status_code == 404
        a.post(f"/r/{code}/api/like/{b_id}", json={"liked": True})
        assert a.get(f"/r/{code}/api/vcard/{b_id}").status_code == 404  # 한쪽만

        res = b.post(f"/r/{code}/api/like/{a_id}", json={"liked": True}).json()
        assert res["phone"] == "010-1111-2222" and res["email"] == "dev@example.com"
        pa = state(a, code)["people"][0]
        assert pa["phone"] == "010-3333-4444" and pa["email"] == "mk@example.com"

        card = a.get(f"/r/{code}/api/vcard/{b_id}")
        assert card.status_code == 200
        assert card.headers["content-type"].startswith("text/vcard")
        # iOS Safari는 attachment면 파일 앱으로 보내고, inline이어야 연락처 추가 화면을 연다.
        assert card.headers["content-disposition"].startswith("inline;")
        assert 'filename="contact.vcf"' in card.headers["content-disposition"]
        assert "filename*=UTF-8''%EB%B0%95" in card.headers["content-disposition"]
        body = card.text
        assert "FN:박마케터" in body
        assert "TEL;TYPE=CELL:010-3333-4444" in body
        assert "EMAIL;TYPE=INTERNET:mk@example.com" in body
        assert "NOTE:Meetpoint · 자사몰 특강 · " in body

        a.post(f"/r/{code}/api/like/{b_id}", json={"liked": False})
        assert a.get(f"/r/{code}/api/vcard/{b_id}").status_code == 404
        assert state(a, code)["people"][0]["phone"] is None


def test_vcard_requires_participant(client):
    _, code = create_room(client)
    assert client.get(f"/r/{code}/api/vcard/1").status_code == 401


def test_join_form_has_ecard_fields(client):
    _, code = create_room(client)
    page = client.get(f"/r/{code}").text
    assert 'name="phone" type="tel"' in page
    assert 'name="email" type="email"' in page
    assert 'id="ecard-preview"' in page
