"""라우트에서 함께 쓰는 도구."""

import io
from pathlib import Path
from urllib.parse import urlsplit

import qrcode
import qrcode.image.svg
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.types import ASGIApp, Receive, Scope, Send

from .broker import Broker
from .config import Settings
from .db import Database
from .matching.ai import AIClient
from .matching.service import MatchingService
from .ratelimit import RateLimiter

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class Services:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        broker: Broker,
        ai: AIClient | None,
        matching: MatchingService,
    ) -> None:
        self.settings = settings
        self.db = db
        self.broker = broker
        self.ai = ai
        self.matching = matching
        # 행사장 참가자는 같은 와이파이, 즉 같은 공인 IP로 들어온다.
        # IP 제한은 스팸을 막는 정도로만 크게 두고, 입장 수는 방 정원으로 제한한다.
        self.room_limiter = RateLimiter(limit=20, window_seconds=3600)
        self.join_limiter = RateLimiter(limit=1000, window_seconds=3600)
        # 한 방에 가짜 참가자를 한꺼번에 밀어 넣지 못하게 방마다 1분에 60명까지 받는다.
        self.room_join_limiter = RateLimiter(limit=60, window_seconds=60)
        # 없는 방 코드는 IP마다 10분에 30번까지. 코드를 차례로 맞혀 보는 것을 막는다.
        self.room_miss_limiter = RateLimiter(limit=30, window_seconds=600)
        self.card_ip_limiter = RateLimiter(limit=600, window_seconds=3600)
        # 명함 읽기는 AI 비용이 드니 방마다 정원의 두 배까지만 허용한다.
        self.card_room_limiter = RateLimiter(limit=2 * settings.max_participants, window_seconds=86400)
        # 추천을 다시 계산하게 하는 소개 수정은 참가자마다 1분에 두 번까지. 오타 한 번 고칠 여유만 둔다.
        self.edit_limiter = RateLimiter(limit=2, window_seconds=60)
        # 운영자 비밀번호를 틀린 IP는 15분에 10번까지.
        self.admin_limiter = RateLimiter(limit=10, window_seconds=900)


def services(request: Request) -> Services:
    return request.app.state.services


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def is_cross_site(request: Request) -> bool:
    """다른 사이트가 보낸 요청인지 브라우저가 붙이는 헤더로 본다. 둘 다 없으면 브라우저 밖(curl, 테스트)이다."""
    site = request.headers.get("sec-fetch-site")
    if site is not None:
        return site not in ("same-origin", "none")
    origin = request.headers.get("origin")
    if origin is None:
        return False
    return urlsplit(origin).netloc != request.headers.get("host")


class CrossSiteGuard:
    """다른 사이트의 폼이나 스크립트로 입장·수정·삭제를 시키지 못하게 GET 외 요청을 막는다(CSRF).
    SSE 같은 GET 응답을 감싸지 않도록 순수 ASGI로 둔다."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] not in ("GET", "HEAD", "OPTIONS"):
            if is_cross_site(Request(scope)):
                await JSONResponse({"error": "cross_site"}, status_code=403)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def public_base(request: Request) -> str:
    configured = services(request).settings.public_base_url.rstrip("/")
    if configured:
        return configured
    return str(request.base_url).rstrip("/")


def is_https(request: Request) -> bool:
    return request.url.scheme == "https" or public_base(request).startswith("https://")


def qr_svg(data: str) -> str:
    qr = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    # XML 선언을 떼어 HTML 안에 바로 넣을 수 있게 한다.
    if svg.startswith("<?xml"):
        svg = svg[svg.index("?>") + 2 :].lstrip()
    return svg
