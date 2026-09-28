"""방 단위 실시간 알림. 단일 프로세스(uvicorn worker 1개)를 전제로 한다."""

import asyncio
from dataclasses import dataclass, field


@dataclass(eq=False)
class Subscriber:
    room_id: int
    participant_id: int | None  # None이면 주최자 화면
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=100))


class Broker:
    def __init__(self) -> None:
        self._rooms: dict[int, set[Subscriber]] = {}

    def subscribe(self, room_id: int, participant_id: int | None) -> Subscriber:
        sub = Subscriber(room_id, participant_id)
        self._rooms.setdefault(room_id, set()).add(sub)
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        subs = self._rooms.get(sub.room_id)
        if subs is None:
            return
        subs.discard(sub)
        if not subs:
            self._rooms.pop(sub.room_id, None)

    def subscriber_count(self, room_id: int) -> int:
        return len(self._rooms.get(room_id, ()))

    def publish(self, room_id: int, event: str, data: dict | None = None, *, to: int | None = None) -> None:
        """to를 주면 그 참가자에게만, 없으면 방 전체(주최자 포함)에 보낸다."""
        for sub in list(self._rooms.get(room_id, ())):
            if to is not None and sub.participant_id != to:
                continue
            try:
                sub.queue.put_nowait((event, data or {}))
            except asyncio.QueueFull:
                # 느린 연결은 건너뛴다. 클라이언트는 다음 이벤트에서 전체 상태를 다시 읽는다.
                pass
