from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./meetpoint.db"
    # 테스트처럼 이벤트 루프가 여러 개일 때만 끈다. 운영에서는 켜 둔다.
    database_pool: bool = True
    # QR과 공유 링크에 쓸 공개 주소. 비워두면 요청 주소를 그대로 쓴다.
    public_base_url: str = ""

    # 운영자 화면(/admin) 비밀번호. 비워두면 운영자 화면이 꺼진다.
    admin_password: str = ""

    # 방을 만들면 관리 주소를 주최자 이메일로 보낸다. smtp_host를 비워두면 보내지 않는다.
    # Gmail은 smtp.gmail.com, 587, 계정 주소와 앱 비밀번호.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    # 보내는 주소. 비워두면 smtp_user.
    mail_from: str = ""

    gemini_api_key: str = ""
    ai_model: str = "gemini-3.8-flash"
    # Gemini thinking_level(minimal, low, medium, high). 현장에서는 기다리는 시간이 중요해서 낮게 둔다.
    # 이유의 질이 아쉬우면 medium으로 올린다.
    ai_effort: str = "low"
    ai_card_effort: str = "low"
    ai_batch_size: int = 20
    ai_concurrency: int = 6
    ai_timeout_seconds: float = 90.0
    # 하루 AI 호출 상한(추천과 명함 읽기를 합친 수). 넘으면 추천은 키워드로 채우고 명함 읽기는 멈춘다.
    ai_daily_limit: int = 10000
    # 방 하나의 하루 추천 호출 상한. 300명이 차례로 들어와도 약 2,300번이라 수정까지 넉넉하다.
    ai_room_daily_limit: int = 3000

    max_participants: int = 300
    max_card_bytes: int = 5 * 1024 * 1024

    # 테스트에서만 켠다. 추천 계산을 백그라운드가 아니라 요청 안에서 끝낸다.
    inline_tasks: bool = False

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def mail_enabled(self) -> bool:
        return bool(self.smtp_host)


@lru_cache
def get_settings() -> Settings:
    return Settings()
