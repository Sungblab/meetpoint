from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select

from .. import repo
from ..models import Participant, utcnow
from ..web import public_base, qr_svg, services, templates
from .api import sse_response

router = APIRouter()


def _gone(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "message.html",
        {"title": "관리 주소가 맞지 않아요", "body": "방을 만들 때 받은 관리 주소로 다시 들어와 주세요. 삭제된 방일 수도 있어요."},
        status_code=404,
    )


@router.get("/h/{token}", response_class=HTMLResponse)
async def dashboard(request: Request, token: str, created: int = 0):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_host_token(s, token)
        if room is None:
            return _gone(request)
    base = public_base(request)
    join_url = f"{base}/r/{room.code}"
    return templates.TemplateResponse(
        request,
        "host.html",
        {
            "room": room,
            "join_url": join_url,
            "host_url": f"{base}/h/{token}",
            "screen_url": f"/s/{room.code}",
            "qr": qr_svg(join_url),
            "token": token,
            "ai_enabled": svc.settings.ai_enabled,
            "mail_enabled": svc.settings.mail_enabled,
        },
    )


@router.get("/h/{token}/api/stats")
async def stats(request: Request, token: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_host_token(s, token)
        if room is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        people = (
            await s.scalars(select(Participant).where(Participant.room_id == room.id).order_by(Participant.id.desc()))
        ).all()
        pairs = await repo.mutual_pairs(s, room.id)
        return {
            "closed": room.is_closed,
            "participants": len(people),
            "pending": sum(1 for p in people if p.recs_status == "pending"),
            "matches": len(pairs),
            "people": [{"name": p.name, "headline": p.headline} for p in people],
        }


@router.get("/h/{token}/events")
async def host_events(request: Request, token: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_host_token(s, token)
        if room is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        room_id = room.id
    return sse_response(request, svc.broker, room_id, None)


async def _set_closed(request: Request, token: str, closed: bool):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_host_token(s, token)
        if room is None:
            return _gone(request)
        room.closed_at = utcnow() if closed else None
        await s.commit()
        svc.broker.publish(room.id, "refresh")
    return RedirectResponse(f"/h/{token}", status_code=303)


@router.post("/h/{token}/close")
async def close_room(request: Request, token: str):
    return await _set_closed(request, token, True)


@router.post("/h/{token}/reopen")
async def reopen_room(request: Request, token: str):
    return await _set_closed(request, token, False)


@router.post("/h/{token}/delete")
async def delete_room(request: Request, token: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_host_token(s, token)
        if room is None:
            return _gone(request)
        room_id = room.id
        await repo.delete_room(s, room_id)
        await s.commit()
    svc.broker.publish(room_id, "gone")
    return templates.TemplateResponse(
        request, "message.html", {"title": "방을 지웠어요", "body": "참가자 정보와 추천, 연결 기록을 모두 지웠어요."}
    )
