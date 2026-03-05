"""
Story 1.1 — GET /health 엔드포인트 테스트
AC #4: Render 배포 후 GET /health → 200 OK {"status": "ok"}
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """헬스체크 응답 상태코드가 200이어야 한다"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    """헬스체크 응답 본문이 {"status": "ok"} 이어야 한다"""
    response = client.get("/api/v1/health")
    assert response.json() == {"status": "ok"}


def test_health_content_type_json():
    """헬스체크 응답 Content-Type이 application/json 이어야 한다"""
    response = client.get("/api/v1/health")
    assert "application/json" in response.headers["content-type"]
