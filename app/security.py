import hashlib
import secrets

# 헷갈리는 글자(0/O, 1/I/L)를 뺀 방 코드 문자
ROOM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_room_code(length: int = 6) -> str:
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(length))


def participant_cookie_name(code: str) -> str:
    return f"mp_{code}"
