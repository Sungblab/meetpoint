"""운영자 화면. 모든 방과 참가자를 본다. 연락처는 보여주지 않는다."""

import secrets
from datetime import UTC, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from .. import repo
from ..models import Like, Participant, Room
from ..web import services, templates

KST = timezone(timedelta(hours=9))
basic = HTTPBasic(auto_error=False)


def require_admin(request: Request, cred: HTTPBasicCredentials | None = Depends(basic)) -> None:
    password = services(request).settings.admin_password
    if not password:
        raise HTTPException(404)
    if cred is None or not secrets.compare_digest(cred.password.encode(), password.encode()):
        raise HTTPException(401, headers={"WWW-Authenticate": 'Basic realm="Meetpoint admin"'})


router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


def kst(value: datetime | None) -> str:
    if value is None:
        return ""
    # SQLite는 시간대 없이 돌려준다. 저장은 늘 UTC다.
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(KST).strftime("%Y-%m-%d %H:%M")


templates.env.filters["kst"] = kst


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        # ponytail: 방을 전부 한 번에 그린다. 수천 개가 되면 페이지를 나눈다.
        rooms = (await s.scalars(select(Room).order_by(Room.id.desc()))).all()
        people = dict((await s.execute(select(Participant.room_id, func.count()).group_by(Participant.room_id))).all())
        back = aliased(Like)
        matches = dict(
            (
                await s.execute(
                    select(Like.room_id, func.count())
                    .join(back, (back.from_id == Like.to_id) & (back.to_id == Like.from_id))
                    .where(Like.from_id < Like.to_id)
                    .group_by(Like.room_id)
                )
            ).all()
        )
        recent = (
            await s.execute(
                select(Participant, Room)
                .join(Room, Room.id == Participant.room_id)
                .order_by(Participant.id.desc())
                .limit(50)
            )
        ).all()
    # 주최자는 이메일로 묶는다. 방은 최신순이라 처음 본 방이 그 주최자의 마지막 방이다.
    hosts: dict[str, dict] = {}
    for room in rooms:
        h = hosts.setdefault(
            room.host_email,
            {"email": room.host_email, "rooms": 0, "people": 0, "last": room.created_at, "marketing": bool(room.marketing_consent_at)},
        )
        h["rooms"] += 1
        h["people"] += people.get(room.id, 0)
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "hosts": sorted(hosts.values(), key=lambda h: -h["rooms"]),
            "rooms": rooms,
            "people": people,
            "matches": matches,
            "recent": recent,
            "totals": (len(rooms), sum(people.values()), sum(matches.values())),
        },
    )


@router.get("/r/{code}", response_class=HTMLResponse)
async def room_detail(request: Request, code: str):
    svc = services(request)
    async with svc.db.sessionmaker() as s:
        room = await repo.room_by_code(s, code)
        if room is None:
            raise HTTPException(404)
        people = (
            await s.scalars(select(Participant).where(Participant.room_id == room.id).order_by(Participant.id))
        ).all()
        likes = await s.scalar(select(func.count()).select_from(Like).where(Like.room_id == room.id)) or 0
        pairs = sorted(await repo.mutual_pairs(s, room.id))
    names = {p.id: p.name for p in people}
    links = {p.id: 0 for p in people}
    for a, b in pairs:
        links[a] += 1
        links[b] += 1
    return templates.TemplateResponse(
        request,
        "admin_room.html",
        {
            "room": room,
            "people": people,
            "likes": likes,
            "links": links,
            "pairs": [(names[a], names[b]) for a, b in pairs],
        },
    )
