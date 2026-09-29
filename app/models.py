from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    host_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300), default="")
    # 관리 주소를 보내고 방 운영 안내를 할 주최자 이메일. 방을 지우면 같이 지워진다.
    host_email: Mapped[str] = mapped_column(String(254), default="")
    # 소식 받기에 동의한 시각(ISO). 비어 있으면 동의하지 않은 것이다. 광고성 메일은 여기 값이 있을 때만 보낸다.
    marketing_consent_at: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(30))
    headline: Mapped[str] = mapped_column(String(60), default="")
    about: Mapped[str] = mapped_column(Text, default="")
    # 같은 분야에서 나보다 잘하는 사람에게 묻고 싶은 것
    ask_same: Mapped[str] = mapped_column(Text, default="")
    # 다른 분야 사람에게 필요한 것
    ask_other: Mapped[str] = mapped_column(Text, default="")
    # 현장에서 나를 알아볼 수 있는 단서. 방 참가자 모두에게 보인다.
    find_me: Mapped[str] = mapped_column(String(60), default="")
    # 서로 만나고 싶다고 누른 사람에게만 보인다.
    contact: Mapped[str] = mapped_column(String(100), default="")
    # pending: 추천 계산 중, ready: 끝남
    recs_status: Mapped[str] = mapped_column(String(10), default="pending")
    profile_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Recommendation(Base):
    """viewer가 target을 봤을 때의 추천. 보는 사람마다 이유가 다르다."""

    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("viewer_id", "target_id", name="uq_rec_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    viewer_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), index=True)
    # common: 같은 분야 고수, complement: 다른 분야 도움, none: 뚜렷한 연결점 없음
    kind: Mapped[str] = mapped_column(String(12))
    score: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(Text, default="")
    opener: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(12), default="heuristic")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("from_id", "to_id", name="uq_like_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    from_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), index=True)
    to_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
