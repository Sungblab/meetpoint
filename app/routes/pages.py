import re

from fastapi import APIRouter, BackgroundTasks, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from .. import repo
from ..mail import send_mail
from ..matching.ai import AIUnavailable
from ..models import Participant, Room, utcnow
from ..security import hash_token, new_room_code, new_token, participant_cookie_name
from ..web import client_ip, is_https, public_base, qr_svg, services, templates

router = APIRouter()

PROFILE_LIMITS = {
    "name": 30,
    "headline": 60,
    "about": 400,
    "ask_same": 300,
    "ask_other": 300,
    "find_me": 60,
    "contact": 100,
}
PROFILE_LABELS = {
    "name": "이름",
    "headline": "한 줄 소개",
    "about": "자기소개",
    "ask_same": "같은 분야에 묻고 싶은 것",
    "ask_other": "다른 분야에서 필요한 것",
    "find_me": "나를 찾는 법",
    "contact": "연락처",
}
SINGLE_LINE = {"name", "headline", "find_me", "contact"}
MATCHING_FIELDS = ("name", "headline", "about", "ask_same", "ask_other")

_CODE_CLEAN = re.compile(r"[^A-Za-z0-9]")
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def clean_profile(form) -> tuple[dict[str, str], list[str]]:
    data: dict[str, str] = {}
    for key in PROFILE_LIMITS:
        raw = str(form.get(key) or "")
        data[key] = " ".join(raw.split()) if key in SINGLE_LINE else raw.strip()
    errors: list[str] = []
    if not data["name"]:
        errors.append("이름을 적어주세요.")
    if not data["about"]:
        errors.append("자기소개를 적어주세요.")
    if not data["ask_same"] and not data["ask_other"]:
        errors.append("같은 분야에 묻고 싶은 것과 다른 분야에서 필요한 것 중 하나는 적어주세요.")
    for key, limit in PROFILE_LIMITS.items():
        if len(data[key]) > limit:
            errors.append(f"{PROFILE_LABELS[key]}은(는) {limit}자까지 쓸 수 있어요.")
    return data, errors


def _set_participant_cookie(response: Response, request: Request, code: str, token: str) -> None:
    response.set_cookie(
        participant_cookie_name(code),
        token,
        # 방을 자동으로 지우지 않으니, 1년 동안 내 명찰을 알아보고 고치거나 지울 수 있게 한다.
        max_age=365 * 86400,
        path=f"/r/{code}",
        httponly=True,
        samesite="lax",
        secure=is_https(request),
    )


def _not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "message.html", {"title": "방을 찾을 수 없어요", "body": "QR이나 주소를 다시 확인해 주세요. 지워진 방일 수도 있어요."}, status_code=404)


async def current_participant(request: Request, s, room: Room) -> Participant | None:
    token = request.cookies.get(participant_cookie_name(room.code))
    return await repo.participant_by_token(s, room, token)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    mail = services(request).settings.mail_enabled
    return templates.TemplateResponse(request, "index.html", {"error": None, "values": {}, "mail_enabled": mail})


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "privacy.html", {})


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(request, "terms.html", {})


@router.get("/join")
async def join_by_code(code: str = ""):
    cleaned = _CODE_CLEAN.sub("", code).upper()
    if not cleaned:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/r/{cleaned}", status_code=303)


@router.post("/rooms")
async def create_room(request: Request):
    svc = services(request)
    form = await request.form()
    name = " ".join(str(form.get("name") or "").split())
    description = str(form.get("description") or "").strip()
    email = str(form.get("email") or "").strip().lower()
    marketing = form.get("marketing") == "1"
    values = {"name": name, "description": description, "email": email, "marketing": marketing}

    def fail(msg: str, status: int = 400):
        ctx = {"error": msg, "values": values, "mail_enabled": svc.settings.mail_enabled}
        return templates.TemplateResponse(request, "index.html", ctx, status_code=status)

    if not name:
        return fail("행사 이름을 적어주세요.")
    if len(email) > 254 or not _EMAIL.fullmatch(email):
        return fail("관리 주소를 받을 이메일을 다시 확인해 주세요.")
    if len(name) > 80 or len(description) > 300:
        return fail("행사 이름은 80자, 설명은 300자까지 쓸 수 있어요.")
    if not svc.room_limiter.allow(client_ip(request)):
        return fail("방을 너무 많이 만들었어요. 잠시 뒤에 다시 시도해 주세요.", 429)

    token = new_token()
    async with svc.db.sessionmaker() as s:
        for _ in range(10):
            code = new_room_code()
            if await repo.room_by_code(s, code) is None:
                break
        room = Room(
            code=code,
            host_token_hash=hash_token(token),
            name=name,
            description=description,
            host_email=email,
            marketing_consent_at=utcnow().isoformat() if marketing else "",
        )
        s.add(room)
        await s.commit()
    background = BackgroundTasks()
    if svc.settings.mail_enabled:
        base = public_base(request)
        body = (
            f"{name} 방을 만들었어요.\n\n"
            f"관리 주소 (주최자 전용이에요. 참가자에게 보여주지 마세요.)\n{base}/h/{token}\n\n"
            f"참가 주소\n{base}/r/{code}\n\n"
            "관리 주소에서 참가 QR과 프로젝터 화면을 열고, 입장을 마감하거나 방을 지울 수 있어요.\n"
            "이 메일은 Meetpoint에서 방을 만들 때 적은 이메일로 보냈어요."
        )
        background.add_task(send_mail, svc.settings, email, f"[Meetpoint] {name} 관리 주소", body)
    return RedirectResponse(f"/h/{token}", status_code=303, background=background)


@router.get("/r/{code}", response_class=HTMLResponse)
async def room_page(request: Request, code: str, left: int = 0):
    if code != code.upper():
        return RedirectResponse(f"/r/{code.upper()}", status_code=307)
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        me = await current_participant(request, s, room)
    if me is not None:
        return templates.TemplateResponse(request, "room.html", {"room": room, "me": me})
    if room.is_closed:
        return templates.TemplateResponse(
            request,
            "message.html",
            {"title": f"{room.name} 입장이 마감됐어요", "body": "주최자가 새 참가를 닫았어요."},
        )
    return templates.TemplateResponse(
        request,
        "join.html",
        {
            "room": room,
            "values": {},
            "errors": [],
            "mode": "join",
            "ai_enabled": svc.settings.ai_enabled,
            "left": bool(left),
        },
    )


@router.post("/r/{code}/join")
async def join_room(request: Request, code: str):
    svc = services(request)
    form = await request.form()
    data, errors = clean_profile(form)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        if await current_participant(request, s, room) is not None:
            return RedirectResponse(f"/r/{code}", status_code=303)
        if room.is_closed:
            errors = ["주최자가 새 참가를 닫았어요."]
        elif await repo.count_participants(s, room.id) >= svc.settings.max_participants:
            errors = ["이 방은 정원이 찼어요."]
        elif not errors and not svc.join_limiter.allow(client_ip(request)):
            errors = ["요청이 너무 많아요. 잠시 뒤에 다시 시도해 주세요."]
        if errors:
            return templates.TemplateResponse(
                request,
                "join.html",
                {
                    "room": room,
                    "values": data,
                    "errors": errors,
                    "mode": "join",
                    "ai_enabled": svc.settings.ai_enabled,
                    "left": False,
                },
                status_code=400,
            )
        token = new_token()
        me = Participant(room_id=room.id, token_hash=hash_token(token), **data)
        s.add(me)
        await s.commit()
        room_id, me_id = room.id, me.id

    response = RedirectResponse(f"/r/{code}", status_code=303)
    _set_participant_cookie(response, request, code, token)
    svc.broker.publish(room_id, "refresh")
    await svc.matching.enqueue(room_id, me_id)
    return response


@router.get("/r/{code}/me", response_class=HTMLResponse)
async def edit_page(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        me = await current_participant(request, s, room)
    if me is None:
        return RedirectResponse(f"/r/{code}", status_code=303)
    values = {k: getattr(me, k) for k in PROFILE_LIMITS}
    return templates.TemplateResponse(
        request,
        "join.html",
        {"room": room, "values": values, "errors": [], "mode": "edit", "ai_enabled": svc.settings.ai_enabled, "left": False},
    )


@router.post("/r/{code}/me")
async def edit_profile(request: Request, code: str):
    svc = services(request)
    form = await request.form()
    data, errors = clean_profile(form)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        me = await current_participant(request, s, room)
        if me is None:
            return RedirectResponse(f"/r/{code}", status_code=303)
        if errors:
            return templates.TemplateResponse(
                request,
                "join.html",
                {"room": room, "values": data, "errors": errors, "mode": "edit", "ai_enabled": svc.settings.ai_enabled, "left": False},
                status_code=400,
            )
        changed = any(getattr(me, k) != data[k] for k in MATCHING_FIELDS)
        for key, value in data.items():
            setattr(me, key, value)
        me.updated_at = utcnow()
        if changed:
            me.profile_version += 1
            me.recs_status = "pending"
        await s.commit()
        room_id, me_id = room.id, me.id

    svc.broker.publish(room_id, "refresh")
    if changed:
        await svc.matching.enqueue(room_id, me_id)
    return RedirectResponse(f"/r/{code}", status_code=303)


@router.post("/r/{code}/leave")
async def leave_room(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        me = await current_participant(request, s, room)
        if me is not None:
            await repo.delete_participant(s, me.id)
            await s.commit()
            svc.broker.publish(room.id, "refresh")
    response = RedirectResponse(f"/r/{code}?left=1", status_code=303)
    response.delete_cookie(participant_cookie_name(code), path=f"/r/{code}")
    return response


def _sniff_image(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return None


@router.post("/r/{code}/card")
async def read_card(request: Request, code: str, file: UploadFile = File(...)):
    svc = services(request)
    if svc.ai is None:
        return JSONResponse({"error": "명함 읽기가 꺼져 있어요. 직접 적어주세요."}, status_code=503)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return JSONResponse({"error": "방을 찾을 수 없어요."}, status_code=404)
    if not svc.card_ip_limiter.allow(client_ip(request)) or not svc.card_room_limiter.allow(code):
        return JSONResponse({"error": "잠시 뒤에 다시 시도해 주세요."}, status_code=429)

    data = await file.read(svc.settings.max_card_bytes + 1)
    if len(data) > svc.settings.max_card_bytes:
        return JSONResponse({"error": "사진이 너무 커요. 5MB 이하로 올려주세요."}, status_code=413)
    media_type = _sniff_image(data)
    if media_type is None:
        return JSONResponse({"error": "JPG, PNG, WEBP 사진만 읽을 수 있어요."}, status_code=415)

    try:
        card = await svc.ai.read_card(data, media_type)
    except AIUnavailable:
        return JSONResponse({"error": "지금은 명함을 읽을 수 없어요. 직접 적어주세요."}, status_code=502)
    if not card.is_business_card:
        return JSONResponse({"error": "명함을 알아보지 못했어요. 밝은 곳에서 다시 찍거나 직접 적어주세요."}, status_code=422)
    # 사진은 저장하지 않는다. 읽은 글자만 돌려준다.
    return JSONResponse(
        {
            "name": card.name[: PROFILE_LIMITS["name"]],
            "headline": card.headline[: PROFILE_LIMITS["headline"]],
            "about": card.about[: PROFILE_LIMITS["about"]],
            "contact": card.contact[: PROFILE_LIMITS["contact"]],
        }
    )


@router.get("/s/{code}", response_class=HTMLResponse)
async def screen(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return _not_found(request)
        count = await repo.count_participants(s, room.id)
    join_url = f"{public_base(request)}/r/{room.code}"
    return templates.TemplateResponse(
        request, "screen.html", {"room": room, "join_url": join_url, "qr": qr_svg(join_url), "count": count}
    )


@router.get("/s/{code}/count")
async def screen_count(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return {"count": await repo.count_participants(s, room.id), "closed": room.is_closed}
