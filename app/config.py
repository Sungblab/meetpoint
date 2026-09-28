from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./meetpoint.db"
    # 테스트처럼 이벤트 루프가 여러 개일 때만 끈다. 운영에서는 켜 둔다.
    database_pool: bool = True
    # QR과 공유 링크에 쓸 공개 주소. 비워두면 요청 주소를 그대로 쓴다.
    public_base_url: str = ""

    anthropic_api_key: str = ""
    ai_model: str = "claude-opus-5"
    # 현장에서는 기다리는 시간이 중요해서 낮게 둔다. 이유의 질이 아쉬우면 medium으로 올린다.
    ai_effort: str = "low"
    ai_card_effort: str = "low"
    # 안전 분류기가 요청을 거절하면 서버에서 다른 모델로 다시 실행한다.
    ai_fallbacks: bool = True
    ai_batch_size: int = 20
    ai_concurrency: int = 6
    ai_timeout_seconds: float = 90.0

    max_participants: int = 300
    room_retention_days: int = 30
    max_card_bytes: int = 5 * 1024 * 1024

    # 테스트에서만 켠다. 추천 계산을 백그라운드가 아니라 요청 안에서 끝낸다.
    inline_tasks: bool = False

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
