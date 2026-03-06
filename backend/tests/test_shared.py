"""
공유 링크 읽기 전용 뷰어 테스트 — Story 4.2
GET /api/v1/shared/{share_token} (인증 불필요) 검증
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """공유 뷰어는 인증 불필요 — dependency override 없이 그대로 사용"""
    from app.main import app
    yield TestClient(app)


def _make_analysis_set(share_token="valid-token"):
    return {
        "id": "set-id-1",
        "name": "삼성전자 분석",
        "owner_id": "user-id-1",
        "company_codes": ["005930"],
        "share_token": share_token,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def test_get_shared_returns_analysis_set(client):
    """유효한 share_token으로 분석 세트 + 재무 데이터 반환"""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        _make_analysis_set()
    ]

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.shared.get_pl_data", return_value=[]):
            with patch("app.api.v1.shared.get_bs_data", return_value=[]):
                with patch("app.api.v1.shared.get_cf_data", return_value=[]):
                    response = client.get("/api/v1/shared/valid-token")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "삼성전자 분석"
    assert "company_codes" in data
    assert "financials" in data


def test_get_shared_not_found(client):
    """존재하지 않는 share_token → 404"""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/shared/invalid-token")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "SHARE_TOKEN_NOT_FOUND"


def test_get_shared_no_auth_required(client):
    """인증 없이 200 반환 — auth가 필요한 엔드포인트와 달리 401이 아닌 200 반환"""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        _make_analysis_set()
    ]

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.shared.get_pl_data", return_value=[]):
            with patch("app.api.v1.shared.get_bs_data", return_value=[]):
                with patch("app.api.v1.shared.get_cf_data", return_value=[]):
                    # Authorization 헤더 없이 요청 → 200 (인증 불필요)
                    shared_response = client.get("/api/v1/shared/valid-token")

    # 인증이 필요한 엔드포인트는 헤더 없이 401 반환
    auth_required_response = client.get("/api/v1/analysis-sets")

    assert shared_response.status_code == 200
    assert auth_required_response.status_code == 401
