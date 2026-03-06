"""
분석 세트 PPT 내보내기 테스트 — Story 6.1
POST /api/v1/analysis-sets/{set_id}/export/ppt
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user

MOCK_BUILDER = type("User", (), {"id": "builder-123"})()
MOCK_OTHER_BUILDER = type("User", (), {"id": "other-builder-456"})()
MOCK_ADMIN = type("User", (), {"id": "admin-999"})()

SET_ID = "set-uuid-001"
OWNER_ID = "builder-123"


@pytest.fixture
def builder_client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_BUILDER
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def other_builder_client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_OTHER_BUILDER
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_supabase_with_set(owner_is_current: bool = True, role: str = "builder"):
    """분석 세트가 존재하는 Supabase mock"""
    m = MagicMock()

    owner_id = OWNER_ID if owner_is_current else "someone-else-999"
    set_data_mock = MagicMock()
    set_data_mock.data = [
        {
            "id": SET_ID,
            "name": "테스트세트",
            "owner_id": owner_id,
            "company_codes": ["CORP001", "CORP002"],
            "share_token": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
    ]

    profile_mock = MagicMock()
    profile_mock.data = [{"role": role}]

    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "analysis_sets":
            t.select.return_value.eq.return_value.execute.return_value = set_data_mock
        elif table_name == "user_profiles":
            t.select.return_value.eq.return_value.execute.return_value = profile_mock
        return t

    m.table.side_effect = table_side_effect
    return m


def _mock_supabase_set_not_found():
    """분석 세트가 없는 Supabase mock"""
    m = MagicMock()

    empty_mock = MagicMock()
    empty_mock.data = []

    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "analysis_sets":
            t.select.return_value.eq.return_value.execute.return_value = empty_mock
        return t

    m.table.side_effect = table_side_effect
    return m


def test_export_ppt_success(builder_client):
    """Builder가 본인 소유 분석 세트 내보내기 → 200, PPT Content-Type, Content-Disposition"""
    mock_supabase = _mock_supabase_with_set(owner_is_current=True)

    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase), \
         patch("app.api.v1.analysis_sets.get_pl_data", return_value=[]), \
         patch("app.api.v1.analysis_sets.generate_analysis_ppt", return_value=b"fake_pptx_content"):
        response = builder_client.post(f"/api/v1/analysis-sets/{SET_ID}/export/ppt")

    assert response.status_code == 200
    assert "openxmlformats-officedocument.presentationml" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "pptx" in response.headers["content-disposition"]
    assert response.content == b"fake_pptx_content"


def test_export_ppt_forbidden(other_builder_client):
    """다른 Builder가 타인 소유 분석 세트 내보내기 → 403"""
    mock_supabase = _mock_supabase_with_set(owner_is_current=False)

    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = other_builder_client.post(f"/api/v1/analysis-sets/{SET_ID}/export/ppt")

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "INSUFFICIENT_PERMISSION"


def test_export_ppt_not_found(builder_client):
    """존재하지 않는 set_id → 404"""
    mock_supabase = _mock_supabase_set_not_found()

    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = builder_client.post("/api/v1/analysis-sets/nonexistent-id/export/ppt")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "ANALYSIS_SET_NOT_FOUND"


def test_export_ppt_admin_can_access_others_set(admin_client):
    """Admin은 타인 소유 분석 세트도 내보내기 가능 → 200 (AC4)"""
    # owner_id는 다른 사람이지만 role=admin
    mock_supabase = _mock_supabase_with_set(owner_is_current=False, role="admin")

    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase), \
         patch("app.api.v1.analysis_sets.get_pl_data", return_value=[]), \
         patch("app.api.v1.analysis_sets.generate_analysis_ppt", return_value=b"admin_pptx"):
        response = admin_client.post(f"/api/v1/analysis-sets/{SET_ID}/export/ppt")

    assert response.status_code == 200
    assert response.content == b"admin_pptx"
