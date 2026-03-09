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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
