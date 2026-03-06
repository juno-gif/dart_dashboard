"""
분석 세트 저장 및 불러오기 테스트 — Story 3.1 + Story 3.2
POST/GET/PATCH/DELETE /api/v1/analysis-sets 동작 검증
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

TEST_USER_ID = "test-user-id"
ADMIN_USER_ID = "admin-user-id"
OTHER_USER_ID = "other-user-id"

SAMPLE_SET = {
    "id": "set-uuid-1",
    "name": "테스트 세트",
    "owner_id": TEST_USER_ID,
    "company_codes": ["005930", "035720"],
    "share_token": None,
    "created_at": "2026-03-06T00:00:00",
    "updated_at": "2026-03-06T00:00:00",
}

SAMPLE_SET_WITH_TOKEN = {
    **SAMPLE_SET,
    "share_token": "existing-share-token-abc123",
}

OTHER_USER_SET = {
    "id": "set-uuid-2",
    "name": "다른 유저 세트",
    "owner_id": OTHER_USER_ID,
    "company_codes": ["000660"],
    "share_token": None,
    "created_at": "2026-03-06T00:00:00",
    "updated_at": "2026-03-06T00:00:00",
}

UPDATED_SET = {
    **SAMPLE_SET,
    "name": "수정된 세트",
    "updated_at": "2026-03-06T01:00:00",
}


def _mock_user():
    user = MagicMock()
    user.id = TEST_USER_ID
    return user


def _mock_admin_user():
    user = MagicMock()
    user.id = ADMIN_USER_ID
    return user


@pytest.fixture
def client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_admin_user
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── 4.2 저장 → 201 + AnalysisSet 반환 ───────────────────
class TestCreateAnalysisSet:
    def test_create_returns_201_with_analysis_set(self, client):
        mock_sb = MagicMock()
        # 중복 체크: 없음
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        # insert 결과
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [SAMPLE_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.post(
                "/api/v1/analysis-sets",
                json={"name": "테스트 세트", "company_codes": ["005930", "035720"]},
            )

        assert res.status_code == 201
        body = res.json()
        assert body["id"] == "set-uuid-1"
        assert body["name"] == "테스트 세트"
        assert body["owner_id"] == TEST_USER_ID
        assert body["company_codes"] == ["005930", "035720"]
        assert "created_at" in body
        assert "updated_at" in body

    # ── 4.3 중복 이름 → 409 NAME_ALREADY_EXISTS ──────────
    def test_duplicate_name_returns_409(self, client):
        mock_sb = MagicMock()
        # 중복 체크: 이미 존재
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-id"}
        ]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.post(
                "/api/v1/analysis-sets",
                json={"name": "테스트 세트", "company_codes": ["005930"]},
            )

        assert res.status_code == 409
        body = res.json()
        assert body["detail"]["error"] == "NAME_ALREADY_EXISTS"

    def test_create_without_company_codes_returns_422(self, client):
        res = client.post("/api/v1/analysis-sets", json={"name": "세트"})
        assert res.status_code == 422

    def test_create_with_empty_name_returns_422(self, client):
        res = client.post("/api/v1/analysis-sets", json={"name": "", "company_codes": ["005930"]})
        assert res.status_code == 422

    def test_create_with_empty_company_codes_returns_422(self, client):
        res = client.post("/api/v1/analysis-sets", json={"name": "세트", "company_codes": []})
        assert res.status_code == 422

    def test_create_with_name_too_long_returns_422(self, client):
        long_name = "a" * 101
        res = client.post("/api/v1/analysis-sets", json={"name": long_name, "company_codes": ["005930"]})
        assert res.status_code == 422

    def test_db_error_on_create_returns_503(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB down")

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.post(
                "/api/v1/analysis-sets",
                json={"name": "테스트 세트", "company_codes": ["005930"]},
            )

        assert res.status_code == 503
        assert res.json()["detail"]["error"] == "DB_UNAVAILABLE"


class TestDbErrors:
    def test_db_error_on_list_returns_503(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception("DB down")

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets")

        assert res.status_code == 503
        assert res.json()["detail"]["error"] == "DB_UNAVAILABLE"

    def test_db_error_on_get_returns_503(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB down")

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets/set-uuid-1")

        assert res.status_code == 503
        assert res.json()["detail"]["error"] == "DB_UNAVAILABLE"


# ── 4.4 목록 조회 → 200 + 리스트 ────────────────────────
class TestListAnalysisSets:
    def test_list_returns_200_with_list(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            SAMPLE_SET
        ]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets")

        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["name"] == "테스트 세트"

    def test_list_empty_returns_200_with_empty_list(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets")

        assert res.status_code == 200
        assert res.json() == []


# ── 4.5 단일 세트 조회 → 200 + AnalysisSet ──────────────
class TestGetAnalysisSet:
    def test_get_returns_200_with_set(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            SAMPLE_SET
        ]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets/set-uuid-1")

        assert res.status_code == 200
        body = res.json()
        assert body["id"] == "set-uuid-1"
        assert body["company_codes"] == ["005930", "035720"]

    def test_get_not_found_returns_404(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/analysis-sets/non-existent-id")

        assert res.status_code == 404
        body = res.json()
        assert body["detail"]["error"] == "ANALYSIS_SET_NOT_FOUND"


# ── Story 3.2: PATCH 수정 테스트 ─────────────────────────
class TestPatchAnalysisSet:
    def test_patch_name_returns_200(self, client):
        mock_sb = MagicMock()
        # 1. 존재 확인: select("*").eq("id").execute()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]
        # 2. 중복 체크: select("id").eq("owner_id").eq("name").execute() → 없음
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        # 3. 업데이트 결과
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [UPDATED_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch(
                f"/api/v1/analysis-sets/{SAMPLE_SET['id']}",
                json={"name": "수정된 세트"},
            )

        assert res.status_code == 200
        assert res.json()["name"] == "수정된 세트"

    def test_patch_company_codes_returns_200(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]
        new_codes_set = {**SAMPLE_SET, "company_codes": ["005930"]}
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [new_codes_set]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch(
                f"/api/v1/analysis-sets/{SAMPLE_SET['id']}",
                json={"company_codes": ["005930"]},
            )

        assert res.status_code == 200
        assert res.json()["company_codes"] == ["005930"]

    def test_patch_no_fields_returns_existing(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch(f"/api/v1/analysis-sets/{SAMPLE_SET['id']}", json={})

        assert res.status_code == 200
        assert res.json()["id"] == SAMPLE_SET["id"]

    def test_patch_not_found_returns_404(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch("/api/v1/analysis-sets/non-existent", json={"name": "새 이름"})

        assert res.status_code == 404
        assert res.json()["detail"]["error"] == "ANALYSIS_SET_NOT_FOUND"

    def test_patch_with_empty_name_returns_422(self, client):
        res = client.patch(
            f"/api/v1/analysis-sets/{SAMPLE_SET['id']}",
            json={"name": ""},
        )
        assert res.status_code == 422

    def test_patch_with_empty_company_codes_returns_422(self, client):
        res = client.patch(
            f"/api/v1/analysis-sets/{SAMPLE_SET['id']}",
            json={"company_codes": []},
        )
        assert res.status_code == 422

    def test_patch_other_owner_returns_403(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [OTHER_USER_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch(
                f"/api/v1/analysis-sets/{OTHER_USER_SET['id']}",
                json={"name": "침입 시도"},
            )

        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "INSUFFICIENT_PERMISSION"

    def test_patch_admin_can_patch_any_set(self, admin_client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [OTHER_USER_SET]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        admin_updated = {**OTHER_USER_SET, "name": "어드민이 수정"}
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [admin_updated]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="admin"):
            res = admin_client.patch(
                f"/api/v1/analysis-sets/{OTHER_USER_SET['id']}",
                json={"name": "어드민이 수정"},
            )

        assert res.status_code == 200
        assert res.json()["name"] == "어드민이 수정"

    def test_patch_duplicate_name_returns_409(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]
        # 중복 체크: 이미 존재
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "another-set"}
        ]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.patch(
                f"/api/v1/analysis-sets/{SAMPLE_SET['id']}",
                json={"name": "기존 이름"},
            )

        assert res.status_code == 409
        assert res.json()["detail"]["error"] == "NAME_ALREADY_EXISTS"


# ── Story 3.2: DELETE 삭제 테스트 ────────────────────────
class TestDeleteAnalysisSet:
    def test_delete_returns_204(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.delete(f"/api/v1/analysis-sets/{SAMPLE_SET['id']}")

        assert res.status_code == 204

    def test_delete_not_found_returns_404(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.delete("/api/v1/analysis-sets/non-existent")

        assert res.status_code == 404
        assert res.json()["detail"]["error"] == "ANALYSIS_SET_NOT_FOUND"

    def test_delete_other_owner_returns_403(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [OTHER_USER_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.delete(f"/api/v1/analysis-sets/{OTHER_USER_SET['id']}")

        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "INSUFFICIENT_PERMISSION"

    def test_delete_admin_can_delete_any_set(self, admin_client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [OTHER_USER_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="admin"):
            res = admin_client.delete(f"/api/v1/analysis-sets/{OTHER_USER_SET['id']}")

        assert res.status_code == 204


# ── Story 4.1: 공유 링크 생성 테스트 ─────────────────────
class TestShareAnalysisSet:
    def test_share_creates_new_token(self, client):
        """share_token이 없을 때 신규 토큰 생성 후 200 반환"""
        mock_sb = MagicMock()
        # select: 세트 존재 (share_token=None)
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]
        # update: 토큰 저장 (반환값 불필요)
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.post(f"/api/v1/analysis-sets/{SAMPLE_SET['id']}/share")

        assert res.status_code == 200
        body = res.json()
        assert "share_token" in body
        assert "share_url" in body
        assert "/shared/" in body["share_url"]
        assert len(body["share_token"]) > 0

    def test_share_reuses_existing_token(self, client):
        """share_token이 이미 존재하면 기존 토큰 재사용 (멱등성)"""
        mock_sb = MagicMock()
        # select: 이미 share_token 있음
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET_WITH_TOKEN]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.post(f"/api/v1/analysis-sets/{SAMPLE_SET_WITH_TOKEN['id']}/share")

        assert res.status_code == 200
        body = res.json()
        assert body["share_token"] == "existing-share-token-abc123"
        # update가 호출되지 않아야 함 (기존 토큰 재사용)
        mock_sb.table.return_value.update.assert_not_called()

    def test_share_rejects_non_owner(self, client):
        """타인 소유 세트 공유 시 403"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [OTHER_USER_SET]

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.post(f"/api/v1/analysis-sets/{OTHER_USER_SET['id']}/share")

        assert res.status_code == 403
        assert res.json()["detail"]["error"] == "INSUFFICIENT_PERMISSION"

    def test_share_not_found(self, client):
        """없는 set_id → 404"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb), \
             patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
            res = client.post("/api/v1/analysis-sets/non-existent-id/share")

        assert res.status_code == 404
        assert res.json()["detail"]["error"] == "ANALYSIS_SET_NOT_FOUND"
