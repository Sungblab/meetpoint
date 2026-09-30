import hashlib
import secrets

# 헷갈리는 글자(0/O, 1/I/L)를 뺀 방 코드 문자
ROOM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_room_code(length: int = 8) -> str:
    # 31자 중 8자리(약 8,500억 가지)라 맞혀 보기 어렵다. 예전에 만든 6자리 방도 그대로 쓴다.
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(length))


def participant_cookie_name(code: str) -> str:
    return f"mp_{code}"
