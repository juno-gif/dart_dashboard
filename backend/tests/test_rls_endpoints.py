"""
RLS 인증 가드 테스트 — Story 2.2 + Story 2.3
토큰 없이 보호된 엔드포인트 접근 시 401 반환 검증
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


class TestAuthGuardEndpoints:
    def test_search_companies_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/search?q=삼성")
        assert response.status_code == 401

    def test_get_financials_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/005930/financials")
        assert response.status_code == 401

    def test_compare_financials_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/compare?codes=005930")
        assert response.status_code == 401

    def test_get_my_profile_without_token_returns_401(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    # Story 2.3: 신규 엔드포인트 401 검증
    def test_invite_user_without_token_returns_401(self, client):
        response = client.post("/api/v1/users/invite", json={"email": "x@x.com", "role": "builder"})
        assert response.status_code == 401

    def test_list_users_without_token_returns_401(self, client):
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_update_role_without_token_returns_401(self, client):
        response = client.patch("/api/v1/users/some-id/role", json={"role": "builder"})
        assert response.status_code == 401

    def test_deactivate_without_token_returns_401(self, client):
        response = client.post("/api/v1/users/some-id/deactivate")
        assert response.status_code == 401

    # Story 3.1: analysis-sets 엔드포인트 401 검증
    def test_create_analysis_set_without_token_returns_401(self, client):
        response = client.post(
            "/api/v1/analysis-sets",
            json={"name": "테스트", "company_codes": ["005930"]},
        )
        assert response.status_code == 401

    def test_list_analysis_sets_without_token_returns_401(self, client):
        response = client.get("/api/v1/analysis-sets")
        assert response.status_code == 401

    def test_get_analysis_set_without_token_returns_401(self, client):
        response = client.get("/api/v1/analysis-sets/some-id")
        assert response.status_code == 401

    # Story 3.2: PATCH/DELETE 401 검증
    def test_patch_analysis_set_without_token_returns_401(self, client):
        response = client.patch("/api/v1/analysis-sets/some-id", json={"name": "새 이름"})
        assert response.status_code == 401

    def test_delete_analysis_set_without_token_returns_401(self, client):
        response = client.delete("/api/v1/analysis-sets/some-id")
        assert response.status_code == 401
