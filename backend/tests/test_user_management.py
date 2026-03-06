"""
팀원 초대 및 역할 관리 테스트 — Story 2.3
Admin 전용 엔드포인트 권한 검증 및 기능 동작 확인
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _mock_admin():
    user = MagicMock()
    user.id = "admin-user-id"
    return user


def _mock_builder():
    user = MagicMock()
    user.id = "builder-user-id"
    return user


@pytest.fixture
def admin_client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_admin
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def builder_client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_builder
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_supabase_admin_mock():
    """Admin 사용자 프로필 반환 mock (require_admin 체크용)"""
    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"role": "admin"}
    ]
    return mock


def _make_supabase_builder_mock():
    """Builder 사용자 프로필 반환 mock (require_admin 체크 실패용)"""
    mock = MagicMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"role": "builder"}
    ]
    return mock


# ── POST /api/v1/users/invite ──────────────────────────────────

def test_admin_can_invite_user(admin_client):
    """Admin이 팀원 초대 → 201 + 초대 메시지 반환"""
    mock_supabase = _make_supabase_admin_mock()

    # invite_user_by_email 응답 mock
    mock_invited_user = MagicMock()
    mock_invited_user.user.id = "new-user-id"
    mock_supabase.auth.admin.invite_user_by_email.return_value = mock_invited_user
    # upsert mock
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = admin_client.post(
                "/api/v1/users/invite",
                json={"email": "newmember@example.com", "role": "builder"},
            )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newmember@example.com"
    assert body["role"] == "builder"
    assert "초대" in body["message"]
    # upsert로 user_profiles에 역할이 기록되었는지 확인
    mock_supabase.table.return_value.upsert.assert_called_once_with(
        {"id": "new-user-id", "role": "builder", "display_name": None}
    )


def test_builder_cannot_invite(builder_client):
    """Builder가 팀원 초대 시도 → 403 INSUFFICIENT_PERMISSION"""
    mock_supabase = _make_supabase_builder_mock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = builder_client.post(
                "/api/v1/users/invite",
                json={"email": "newmember@example.com", "role": "builder"},
            )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error"] == "INSUFFICIENT_PERMISSION"


def test_invite_rejects_admin_role(admin_client):
    """admin 역할로 초대 시도 → 422 (InviteRoleType 검증)"""
    mock_supabase = _make_supabase_admin_mock()
    with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = admin_client.post(
            "/api/v1/users/invite",
            json={"email": "hacker@example.com", "role": "admin"},
        )
    assert response.status_code == 422


# ── PATCH /api/v1/users/{user_id}/role ────────────────────────

def test_admin_can_update_role(admin_client):
    """Admin이 팀원 역할 변경 → 200 + 업데이트된 UserProfile"""
    mock_supabase = _make_supabase_admin_mock()
    updated_profile = {"id": "target-user-id", "role": "live_viewer", "display_name": None}
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        updated_profile
    ]

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = admin_client.patch(
                "/api/v1/users/target-user-id/role",
                json={"role": "live_viewer"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "live_viewer"


def test_non_admin_cannot_update_role(builder_client):
    """Builder가 역할 변경 시도 → 403 INSUFFICIENT_PERMISSION"""
    mock_supabase = _make_supabase_builder_mock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = builder_client.patch(
                "/api/v1/users/target-user-id/role",
                json={"role": "read_only"},
            )

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error"] == "INSUFFICIENT_PERMISSION"


# ── POST /api/v1/users/{user_id}/deactivate ───────────────────

def test_admin_can_deactivate_user(admin_client):
    """Admin이 팀원 비활성화 → 200 + 비활성화 메시지"""
    mock_supabase = _make_supabase_admin_mock()
    mock_supabase.auth.admin.update_user_by_id.return_value = MagicMock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = admin_client.post("/api/v1/users/target-user-id/deactivate")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "target-user-id"
    assert "비활성화" in body["message"]
    # banned_until으로 Supabase API 호출 확인
    mock_supabase.auth.admin.update_user_by_id.assert_called_once_with(
        "target-user-id",
        {"banned_until": "2099-12-31T23:59:59Z"},
    )


def test_non_admin_cannot_deactivate(builder_client):
    """Builder가 비활성화 시도 → 403 INSUFFICIENT_PERMISSION"""
    mock_supabase = _make_supabase_builder_mock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = builder_client.post("/api/v1/users/target-user-id/deactivate")

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["error"] == "INSUFFICIENT_PERMISSION"


# ── GET /api/v1/users ──────────────────────────────────────────

def test_admin_can_list_users(admin_client):
    """Admin이 팀원 목록 조회 → 200 + UserProfile 리스트"""
    mock_supabase = _make_supabase_admin_mock()
    user_list = [
        {"id": "user-1", "role": "admin", "display_name": "Admin"},
        {"id": "user-2", "role": "builder", "display_name": None},
    ]
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = user_list

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = admin_client.get("/api/v1/users")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["role"] == "admin"


def test_builder_cannot_list_users(builder_client):
    """Builder가 팀원 목록 조회 시도 → 403 INSUFFICIENT_PERMISSION"""
    mock_supabase = _make_supabase_builder_mock()

    with patch("app.api.v1.users.get_supabase_client", return_value=mock_supabase):
        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            response = builder_client.get("/api/v1/users")

    assert response.status_code == 403
