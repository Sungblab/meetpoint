import asyncio
import json
from datetime import UTC, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy import select

from .. import repo
from ..broker import Broker
from ..models import Like, Participant, Recommendation
from ..vcard import build_vcard, vcard_disposition
from ..web import services
from .pages import current_participant

router = APIRouter()

KEEPALIVE_SECONDS = 15
KST = timezone(timedelta(hours=9))


def sse_response(request: Request, broker: Broker, room_id: int, participant_id: int | None) -> StreamingResponse:
    sub = broker.subscribe(room_id, participant_id)

    async def stream():
        try:
            yield "retry: 3000\n\n"
            yield "event: hello\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event, data = await asyncio.wait_for(sub.queue.get(), timeout=KEEPALIVE_SECONDS)
                except TimeoutError:
                    yield ": ping\n\n"
                    continue
                yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        finally:
            broker.unsubscribe(sub)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _rec_json(rec: Recommendation | None) -> dict | None:
    if rec is None:
        return None
    return {
        "kind": rec.kind,
        "score": rec.score,
        "reason": rec.reason,
        "opener": rec.opener,
        "source": rec.source,
    }


def _sort_key(item: dict):
    rec = item["rec"]
    if rec is not None and rec["kind"] != "none":
        return (0, -rec["score"], item["id"])
    if item["pending"]:
        return (1, 0, item["id"])
    return (2, -(rec["score"] if rec else 0), item["id"])


async def build_state(s, room, me: Participant) -> dict:
    people = (
        await s.scalars(
            select(Participant).where(Participant.room_id == room.id, Participant.id != me.id).order_by(Participant.id)
        )
    ).all()
    recs = {
        r.target_id: r
        for r in (await s.scalars(select(Recommendation).where(Recommendation.viewer_id == me.id))).all()
    }
    my_likes = set((await s.scalars(select(Like.to_id).where(Like.from_id == me.id))).all())
    liked_me = set((await s.scalars(select(Like.from_id).where(Like.to_id == me.id))).all())

    items = []
    for p in people:
        matched = p.id in my_likes and p.id in liked_me
        rec = recs.get(p.id)
        pending = rec is None and (me.recs_status == "pending" or p.recs_status == "pending")
        items.append(
            {
                "id": p.id,
                "name": p.name,
                "company": p.company,
                "job_title": p.job_title,
                "headline": p.headline,
                "about": p.about,
                "ask_same": p.ask_same,
                "ask_other": p.ask_other,
                "find_me": p.find_me,
                "liked": p.id in my_likes,
                "matched": matched,
                "phone": p.phone if matched else None,
                "email": p.email if matched else None,
                "contact": p.contact if matched else None,
                "rec": _rec_json(rec),
                "pending": pending,
            }
        )
    items.sort(key=_sort_key)
    return {
        "room": {"code": room.code, "name": room.name, "description": room.description, "closed": room.is_closed},
        "me": {"id": me.id, "name": me.name, "headline": me.headline, "recs_status": me.recs_status},
        "people": items,
        "counts": {
            "people": len(items),
            "matches": sum(1 for i in items if i["matched"]),
        },
    }


async def _auth(request: Request, s, code: str):
    room = await repo.room_by_code(s, code)
    me = await current_participant(request, s, room) if room is not None else None
    return room, me


async def _is_matched(s, a: int, b: int) -> bool:
    mine = await s.scalar(select(Like.id).where(Like.from_id == a, Like.to_id == b))
    theirs = await s.scalar(select(Like.id).where(Like.from_id == b, Like.to_id == a))
    return mine is not None and theirs is not None


@router.get("/r/{code}/api/state")
async def state(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room, me = await _auth(request, s, code)
        if room is None or me is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await build_state(s, room, me)


@router.post("/r/{code}/api/like/{target_id}")
async def like(request: Request, code: str, target_id: int):
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        body = {}
    want = bool(body.get("liked", True)) if isinstance(body, dict) else True

    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room, me = await _auth(request, s, code)
        if room is None or me is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        target = await s.get(Participant, target_id)
        if target is None or target.room_id != room.id or target.id == me.id:
            return JSONResponse({"error": "not_found"}, status_code=404)

        existing = await s.scalar(select(Like).where(Like.from_id == me.id, Like.to_id == target.id))
        reverse = await s.scalar(select(Like).where(Like.from_id == target.id, Like.to_id == me.id))
        was_matched = existing is not None and reverse is not None
        if want and existing is None:
            s.add(Like(room_id=room.id, from_id=me.id, to_id=target.id))
        elif not want and existing is not None:
            await s.delete(existing)
        await s.commit()
        matched = want and reverse is not None
        room_id, me_id, me_name = room.id, me.id, me.name
        target_name, target_contact = target.name, target.contact
        target_phone, target_email = target.phone, target.email

    if matched and not was_matched:
        svc.broker.publish(room_id, "match", {"id": me_id, "name": me_name}, to=target_id)
        svc.broker.publish(room_id, "refresh", to=target_id)
    elif was_matched and not matched:
        svc.broker.publish(room_id, "refresh", to=target_id)
    # 주최자 화면의 연결 수를 갱신한다.
    svc.broker.publish(room_id, "stats")
    return {
        "liked": want,
        "matched": matched,
        "name": target_name,
        "contact": target_contact if matched else None,
        "phone": target_phone if matched else None,
        "email": target_email if matched else None,
    }


@router.get("/r/{code}/api/vcard/{target_id}")
async def vcard(request: Request, code: str, target_id: int):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room, me = await _auth(request, s, code)
        if room is None or me is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        target = await s.get(Participant, target_id)
        if target is None or target.room_id != room.id or not await _is_matched(s, me.id, target.id):
            return JSONResponse({"error": "not_found"}, status_code=404)
        rec = await s.scalar(
            select(Recommendation).where(Recommendation.viewer_id == me.id, Recommendation.target_id == target.id)
        )
        created = room.created_at if room.created_at.tzinfo else room.created_at.replace(tzinfo=UTC)
        note = f"Meetpoint · {room.name} · {created.astimezone(KST):%Y-%m-%d}"
        if rec is not None and rec.reason:
            note += f" · 만난 이유: {rec.reason}"
        body = build_vcard(name=target.name, company=target.company, job_title=target.job_title,
                           headline=target.headline, phone=target.phone, email=target.email, other=target.contact,
                           note=note)
        name = target.name
    return Response(body, media_type="text/vcard; charset=utf-8",
                    headers={"Content-Disposition": vcard_disposition(name), "Cache-Control": "no-store"})


@router.get("/r/{code}/api/events")
async def events(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room, me = await _auth(request, s, code)
        if room is None or me is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        room_id, me_id = room.id, me.id
    return sse_response(request, svc.broker, room_id, me_id)
