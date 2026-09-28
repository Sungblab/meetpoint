from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Like, Participant, Recommendation, Room
from .security import hash_token


async def room_by_code(s: AsyncSession, code: str) -> Room | None:
    return await s.scalar(select(Room).where(Room.code == code))


async def room_by_host_token(s: AsyncSession, token: str) -> Room | None:
    return await s.scalar(select(Room).where(Room.host_token_hash == hash_token(token)))


async def participant_by_token(s: AsyncSession, room: Room, token: str | None) -> Participant | None:
    if not token:
        return None
    return await s.scalar(
        select(Participant).where(Participant.room_id == room.id, Participant.token_hash == hash_token(token))
    )


async def count_participants(s: AsyncSession, room_id: int) -> int:
    return await s.scalar(select(func.count()).select_from(Participant).where(Participant.room_id == room_id)) or 0


async def mutual_pairs(s: AsyncSession, room_id: int) -> set[tuple[int, int]]:
    likes = (await s.execute(select(Like.from_id, Like.to_id).where(Like.room_id == room_id))).all()
    edges = {(a, b) for a, b in likes}
    return {(a, b) for a, b in edges if a < b and (b, a) in edges}


async def delete_participant(s: AsyncSession, participant_id: int) -> None:
    await s.execute(delete(Like).where((Like.from_id == participant_id) | (Like.to_id == participant_id)))
    await s.execute(
        delete(Recommendation).where(
            (Recommendation.viewer_id == participant_id) | (Recommendation.target_id == participant_id)
        )
    )
    await s.execute(delete(Participant).where(Participant.id == participant_id))


async def delete_room(s: AsyncSession, room_id: int) -> None:
    await s.execute(delete(Like).where(Like.room_id == room_id))
    await s.execute(delete(Recommendation).where(Recommendation.room_id == room_id))
    await s.execute(delete(Participant).where(Participant.room_id == room_id))
    await s.execute(delete(Room).where(Room.id == room_id))
