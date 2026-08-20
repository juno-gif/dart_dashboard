"""
환경변수 설정 (pydantic-settings)
모든 환경변수는 이 파일을 통해서만 접근 — 직접 os.environ 접근 금지
[Source: architecture.md - 환경 변수 구조]
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DART_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    DATABASE_URL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_API_KEY: str = ""
    # pg_cron → 백엔드 sync 엔드포인트 인증용 시크릿 (랜덤 문자열, 미설정 시 sync/all 비활성화)
    SYNC_SECRET_KEY: str = ""
    # 공공데이터포털 국민연금공단 API (Decoding 인증키) — 감사보고서만 제출하는 비상장사 임직원수 폴백용
    # 미설정 시 폴백 비활성화 (dart_report만 시도)
    NPS_API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
