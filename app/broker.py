"""방 단위 실시간 알림. 단일 프로세스(uvicorn worker 1개)를 전제로 한다."""

import asyncio
from dataclasses import dataclass, field


@dataclass(eq=False)
class Subscriber:
    room_id: int
    participant_id: int | None  # None이면 주최자 화면
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=100))


class Broker:
    def __init__(self, per_client: int = 3, total: int = 2000) -> None:
        # 연결을 끝없이 열어 서버와 Nginx를 막지 못하게, 참가자(주최자는 방)마다와 전체 연결 수를 제한한다.
        self.per_client = per_client
        self.total = total
        self._rooms: dict[int, set[Subscriber]] = {}
        # 구독 순서. 한도를 넘으면 가장 오래된 연결부터 닫는다.
        self._all: dict[Subscriber, None] = {}

    def subscribe(self, room_id: int, participant_id: int | None) -> Subscriber:
        mine = [s for s in self._all if s.room_id == room_id and s.participant_id == participant_id]
        if len(mine) >= self.per_client:
            self.close(mine[0])
        if len(self._all) >= self.total:
            self.close(next(iter(self._all)))
        sub = Subscriber(room_id, participant_id)
        self._rooms.setdefault(room_id, set()).add(sub)
        self._all[sub] = None
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        self._all.pop(sub, None)
        subs = self._rooms.get(sub.room_id)
        if subs is None:
            return
        subs.discard(sub)
        if not subs:
            self._rooms.pop(sub.room_id, None)

    def close(self, sub: Subscriber) -> None:
        """구독을 끊고 연결에 closed 이벤트를 보낸다. 화면은 이 이벤트를 받으면 다시 붙지 않는다."""
        self.unsubscribe(sub)
        while not sub.queue.empty():
            sub.queue.get_nowait()
        sub.queue.put_nowait(("closed", {}))

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
