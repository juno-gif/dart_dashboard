"""
AppPaaS Django 빌드팩 호환용 WSGI 진입점.
uWSGI → a2wsgi(ASGI→WSGI 브릿지) → FastAPI(ASGI) 순으로 연결.
"""
import sys
import os

# backend/ 디렉토리를 Python 경로에 추가 (컨테이너 내 /app 기준)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.main import app as fastapi_app  # noqa: E402
from a2wsgi import ASGIMiddleware        # noqa: E402

# uWSGI가 찾는 WSGI callable
application = ASGIMiddleware(fastapi_app)
