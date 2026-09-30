import time
from collections import deque


class RateLimiter:
    """프로세스 메모리에 두는 간단한 고정 창 제한. 단일 worker 전제."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def blocked(self, key: str) -> bool:
        """기록하지 않고 한도에 닿았는지만 본다. 실패만 세는 제한(없는 방 코드, 틀린 비밀번호)에 쓴다."""
        hits = self._hits.get(key)
        if not hits:
            return False
        now = time.monotonic()
        while hits and now - hits[0] > self.window:
            hits.popleft()
        return len(hits) >= self.limit

    def allow(self, key: str) -> bool:
        if self.blocked(key):
            return False
        now = time.monotonic()
        self._hits.setdefault(key, deque()).append(now)
        if len(self._hits) > 10_000:
            self._hits = {k: v for k, v in self._hits.items() if v and now - v[-1] <= self.window}
        return True
