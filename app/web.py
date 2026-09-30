"""라우트에서 함께 쓰는 도구."""

import io
from pathlib import Path

import qrcode
import qrcode.image.svg
from fastapi import Request
from fastapi.templating import Jinja2Templates

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
        self.card_ip_limiter = RateLimiter(limit=600, window_seconds=3600)
        # 명함 읽기는 AI 비용이 드니 방마다 정원의 두 배까지만 허용한다.
        self.card_room_limiter = RateLimiter(limit=2 * settings.max_participants, window_seconds=86400)
        # 추천을 다시 계산하게 하는 소개 수정은 참가자마다 1분에 두 번까지. 오타 한 번 고칠 여유만 둔다.
        self.edit_limiter = RateLimiter(limit=2, window_seconds=60)


def services(request: Request) -> Services:
    return request.app.state.services


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


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
