"""추천 계산 작업. 참가자가 들어오거나 프로필을 고치면 그 사람과 방의 다른 모두를 양방향으로 평가한다."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError

from ..broker import Broker
from ..config import Settings
from ..db import Database
from ..models import Participant, Recommendation, Room, utcnow
from ..repo import delete_room
from . import heuristic
from .ai import AIClient, AIUnavailable
from .schemas import PairResult, Profile

log = logging.getLogger(__name__)


def to_profile(p: Participant) -> Profile:
    return Profile(
        id=p.id,
        name=p.name,
        company=p.company,
        job_title=p.job_title,
        headline=p.headline,
        about=p.about,
        ask_same=p.ask_same,
        ask_other=p.ask_other,
        version=p.profile_version,
    )


class MatchingService:
    def __init__(self, db: Database, broker: Broker, settings: Settings, ai: AIClient | None) -> None:
        self.db = db
        self.broker = broker
        self.settings = settings
        self.ai = ai
        self._tasks: set[asyncio.Task] = set()
        self._ai_slots = asyncio.Semaphore(max(1, settings.ai_concurrency))

    async def enqueue(self, room_id: int, participant_id: int) -> None:
        if self.settings.inline_tasks:
            await self.run(room_id, participant_id)
            return
        task = asyncio.create_task(self.run(room_id, participant_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def wait_idle(self) -> None:
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    async def run(self, room_id: int, participant_id: int) -> None:
        try:
            await self._run(room_id, participant_id)
        except Exception:
            log.exception("recommendation job failed room=%s participant=%s", room_id, participant_id)

    async def _run(self, room_id: int, participant_id: int) -> None:
        async with self.db.sessionmaker() as s:
            me = await s.get(Participant, participant_id)
            if me is None or me.room_id != room_id:
                return
            new = to_profile(me)
            rows = (
                await s.scalars(
                    select(Participant)
                    .where(Participant.room_id == room_id, Participant.id != participant_id)
                    .order_by(Participant.id)
                )
            ).all()
            others = [to_profile(p) for p in rows]

        size = max(1, self.settings.ai_batch_size)
        for start in range(0, len(others), size):
            batch = others[start : start + size]
            results = await self._evaluate(new, batch)
            await self._save(room_id, new, batch, results)
            for pid in (new.id, *(c.id for c in batch)):
                self.broker.publish(room_id, "refresh", to=pid)

        async with self.db.sessionmaker() as s:
            me = await s.get(Participant, participant_id)
            if me is not None and me.profile_version == new.version:
                me.recs_status = "ready"
                await s.commit()
        self.broker.publish(room_id, "refresh", to=participant_id)
        # 주최자 화면의 "추천 계산 중" 숫자를 갱신한다. 참가자 화면은 이 이벤트를 무시한다.
        self.broker.publish(room_id, "stats")

    async def _evaluate(self, new: Profile, batch: list[Profile]) -> dict[int, tuple[PairResult, PairResult]]:
        results: dict[int, tuple[PairResult, PairResult]] = {}
        if self.ai is not None:
            try:
                async with self._ai_slots:
                    results = await self.ai.recommend(new, batch)
            except AIUnavailable as e:
                log.warning("AI recommendation unavailable (%s); using keyword fallback", e)
            except Exception:
                log.exception("AI recommendation crashed; using keyword fallback")
        for c in batch:
            if c.id not in results:
                results[c.id] = (heuristic.score_pair(new, c), heuristic.score_pair(c, new))
        return results

    async def _save(
        self,
        room_id: int,
        new: Profile,
        batch: list[Profile],
        results: dict[int, tuple[PairResult, PairResult]],
    ) -> None:
        for attempt in range(2):
            try:
                await self._save_once(room_id, new, batch, results)
                return
            except IntegrityError:
                # 같은 쌍을 다른 작업이 동시에 넣었다. 한 번 더 시도하면 update로 처리된다.
                if attempt == 1:
                    raise

    async def _save_once(
        self,
        room_id: int,
        new: Profile,
        batch: list[Profile],
        results: dict[int, tuple[PairResult, PairResult]],
    ) -> None:
        ids = [c.id for c in batch]
        async with self.db.sessionmaker() as s:
            current = {
                p.id: p.profile_version
                for p in (await s.scalars(select(Participant).where(Participant.id.in_([new.id, *ids])))).all()
            }
            # 평가하는 동안 프로필이 바뀌었으면 쓰지 않는다. 바뀐 쪽의 새 작업이 다시 계산한다.
            if current.get(new.id) != new.version:
                return
            existing = {
                (r.viewer_id, r.target_id): r
                for r in (
                    await s.scalars(
                        select(Recommendation).where(
                            or_(
                                and_(Recommendation.viewer_id == new.id, Recommendation.target_id.in_(ids)),
                                and_(Recommendation.target_id == new.id, Recommendation.viewer_id.in_(ids)),
                            )
                        )
                    )
                ).all()
            }
            now = utcnow()
            for c in batch:
                if current.get(c.id) != c.version:
                    continue
                forward, backward = results[c.id]
                for viewer, target, pair in ((new.id, c.id, forward), (c.id, new.id, backward)):
                    row = existing.get((viewer, target))
                    if row is None:
                        row = Recommendation(room_id=room_id, viewer_id=viewer, target_id=target)
                        s.add(row)
                    row.kind = pair.kind
                    row.score = pair.score
                    row.reason = pair.reason
                    row.opener = pair.opener
                    row.source = pair.source
                    row.updated_at = now
            await s.commit()


# 이 시각(2026-09-30 00:00 KST) 전에 만든 방은 "30일 뒤 지운다"는 안내를 보고 들어왔으니 약속대로 지운다.
# 그 뒤로 만든 방은 지우지 않는다. 2026-10-30이 지나면 지울 방이 없으니 이 함수와 호출을 지워도 된다.
LEGACY_BEFORE = datetime(2026, 9, 29, 15, tzinfo=UTC)


async def purge_legacy_rooms(db: Database, legacy_before: datetime = LEGACY_BEFORE) -> int:
    """30일 보관을 약속하고 만든 방 중 30일이 지난 방과 그 안의 모든 참가자 정보를 지운다."""
    cutoff = min(legacy_before, datetime.now(UTC) - timedelta(days=30))
    async with db.sessionmaker() as s:
        ids = (await s.scalars(select(Room.id).where(Room.created_at < cutoff))).all()
        for room_id in ids:
            await delete_room(s, room_id)
        await s.commit()
        return len(ids)
