import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppSettings(BaseSettings):
    """
    Interactive Video Study Guide System 중앙 집중식 애플리케이션 설정
    .env 파일 및 OS 환경변수로부터 로드하고 타입을 자동 검증합니다.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 기본 환경 정보
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    
    # AI 모델 설정
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    selected_gemini_version: str = Field(default="gemini-3.5-flash-lite", alias="SELECTED_GEMINI_VERSION")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    cerebras_api_key: Optional[str] = Field(default=None, alias="CEREBRAS_API_KEY")
    glm_api_key: Optional[str] = Field(default=None, alias="GLM_API_KEY")
    nemotron_3_ultra_api_key: Optional[str] = Field(default=None, alias="NEMOTRON_3_ULTRA_API_KEY")
    jina_api_key: Optional[str] = Field(default=None, alias="JINA_API_KEY")
    unsplash_access_key: Optional[str] = Field(default=None, alias="UNSPLASH_ACCESS_KEY")

    # 작업 및 파이프라인 동시성 제어
    chapter_generation_concurrency: int = Field(default=3, alias="CHAPTER_GENERATION_CONCURRENCY")
    batch_cooldown_seconds: float = Field(default=1.0, alias="BATCH_COOLDOWN_SECONDS")

    # 데이터베이스 및 캐시
    database_url: str = Field(default="sqlite:///./backend/data/jobs.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")

    # 인증 및 보안
    supabase_jwt_secret: str = Field(default="", alias="SUPABASE_JWT_SECRET")
    disable_auth: bool = Field(default=False, alias="DISABLE_AUTH")
    admin_sync_secret: str = Field(default="", alias="ADMIN_SYNC_SECRET")
    prod_backend_url: str = Field(default="", alias="PROD_BACKEND_URL")

    # YouTube 관련 설정
    youtube_cookies_text: Optional[str] = Field(default=None, alias="YOUTUBE_COOKIES_TEXT")
    youtube_innertube_key: Optional[str] = Field(default=None, alias="YOUTUBE_INNERTUBE_KEY")

    def get_celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url or "redis://localhost:6379/0"

    def get_celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url or "redis://localhost:6379/0"

    def validate_keys_on_startup(self) -> list[str]:
        """필수 API 키 및 보안 설정 존재 여부를 확인하고 경고 목록을 반환합니다."""
        warnings = []
        is_prod = self.app_env.lower() in ("production", "prod")

        if not self.gemini_api_key and not self.groq_api_key and not self.openrouter_api_key and not self.openai_api_key:
            warnings.append("[Settings Warning] AI 제공자 API 키(Gemini/Groq/OpenRouter/OpenAI)가 하나도 설정되지 않았습니다.")
        elif not self.gemini_api_key:
            warnings.append("[Settings Info] GEMINI_API_KEY가 없습니다. 대체 AI 제공자(Groq/OpenRouter/OpenAI 등)를 사용합니다.")

        if not self.supabase_jwt_secret or not self.supabase_jwt_secret.strip():
            if is_prod:
                warnings.append("[CRITICAL SECURITY] 프로덕션 환경에서 SUPABASE_JWT_SECRET이 누락되었습니다! 인증이 필요한 모든 API 호출이 500 에러로 차단됩니다.")
            else:
                warnings.append("[Settings Warning] SUPABASE_JWT_SECRET이 설정되지 않았습니다 (로컬 개발 환경).")

        return warnings

# 전역 싱글톤 설정 인스턴스
settings = AppSettings()
