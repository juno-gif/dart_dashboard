"""
비상장사 Admin 편집 테스트 — Story 5.2
GET /api/v1/companies/{corp_code}/manual — 기존 재무 데이터 조회
PUT /api/v1/companies/{corp_code}/manual — Admin 재무 데이터 수정
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user

MOCK_ADMIN = type("User", (), {"id": "admin-123"})()
MOCK_BUILDER = type("User", (), {"id": "builder-456"})()


@pytest.fixture
def admin_client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def builder_client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_BUILDER
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_supabase_with_company(corp_code="MAN_TEST123"):
    """비상장사 + 재무 데이터가 존재하는 mock"""
    m = MagicMock()

    # require_admin용 user_profiles 조회 → admin 반환
    admin_profile_mock = MagicMock()
    admin_profile_mock.data = [{"role": "admin"}]

    # companies 조회 → 비상장사 반환
    company_mock = MagicMock()
    company_mock.data = [{"corp_code": corp_code, "company_name": "테스트비상장(주)"}]

    # financial_statements 조회 → PL 데이터 반환
    financials_mock = MagicMock()
    financials_mock.data = [
        {"bsns_year": "2024", "account_key": "revenue", "amount": 50000000000},
        {"bsns_year": "2024", "account_key": "operating_profit", "amount": 5000000000},
        {"bsns_year": "2024", "account_key": "net_income", "amount": 3000000000},
        {"bsns_year": "2023", "account_key": "revenue", "amount": 40000000000},
    ]

    # upsert mock
    upsert_mock = MagicMock()
    upsert_mock.execute.return_value.data = [{}]

    # 체이닝 설정
    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "user_profiles":
            t.select.return_value.eq.return_value.execute.return_value = admin_profile_mock
        elif table_name == "companies":
            chain = MagicMock()
            chain.eq.return_value.eq.return_value.limit.return_value.execute.return_value = company_mock
            chain.select = MagicMock(return_value=chain)
            t.select = MagicMock(return_value=chain)
        elif table_name == "financial_statements":
            chain = MagicMock()
            chain.eq.return_value.eq.return_value.eq.return_value.execute.return_value = financials_mock
            chain.select = MagicMock(return_value=chain)
            t.select = MagicMock(return_value=chain)
            t.upsert = MagicMock(return_value=upsert_mock)
            # DELETE chain: .delete().eq().eq().eq().execute()
            delete_chain = MagicMock()
            delete_chain.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
            t.delete = MagicMock(return_value=delete_chain)
        return t

    m.table.side_effect = table_side_effect
    return m


def _mock_supabase_company_not_found():
    """비상장사 없는 상태 mock"""
    m = MagicMock()
    empty_mock = MagicMock()
    empty_mock.data = []

    admin_profile_mock = MagicMock()
    admin_profile_mock.data = [{"role": "admin"}]

    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "user_profiles":
            t.select.return_value.eq.return_value.execute.return_value = admin_profile_mock
        elif table_name == "companies":
            chain = MagicMock()
            chain.eq.return_value.eq.return_value.limit.return_value.execute.return_value = empty_mock
            chain.select = MagicMock(return_value=chain)
            t.select = MagicMock(return_value=chain)
        return t

    m.table.side_effect = table_side_effect
    return m


def _mock_supabase_non_admin():
    """Admin 아닌 사용자 mock"""
    m = MagicMock()
    builder_profile_mock = MagicMock()
    builder_profile_mock.data = [{"role": "builder"}]

    def table_side_effect(table_name):
        t = MagicMock()
        if table_name == "user_profiles":
            t.select.return_value.eq.return_value.execute.return_value = builder_profile_mock
        return t

    m.table.side_effect = table_side_effect
    return m


def test_get_manual_company_financials_success(admin_client):
    """Admin GET → 200, ManualCompanyFinancialsResponse 반환"""
    mock_supabase = _mock_supabase_with_company("MAN_TEST123")

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = admin_client.get("/api/v1/companies/MAN_TEST123/manual")

    assert response.status_code == 200
    data = response.json()
    assert data["corp_code"] == "MAN_TEST123"
    assert data["company_name"] == "테스트비상장(주)"
    assert len(data["financials"]) == 2  # 2024, 2023 두 연도
    years = [f["bsns_year"] for f in data["financials"]]
    assert "2024" in years
    assert "2023" in years


def test_get_manual_company_financials_not_found(admin_client):
    """존재하지 않는 corp_code → 404"""
    mock_supabase = _mock_supabase_company_not_found()

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = admin_client.get("/api/v1/companies/MAN_NOTEXIST/manual")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "COMPANY_NOT_FOUND"


def test_get_manual_company_financials_non_admin_forbidden(builder_client):
    """Admin 아닌 사용자 GET → 403"""
    mock_supabase = _mock_supabase_non_admin()

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = builder_client.get("/api/v1/companies/MAN_TEST123/manual")

    assert response.status_code == 403


def test_put_manual_company_success(admin_client):
    """Admin PUT → 200, 재무 데이터 UPSERT"""
    payload = {
        "company_name": "테스트비상장(주)",
        "financials": [
            {"bsns_year": "2024", "revenue": 60000000000, "operating_profit": 6000000000, "net_income": 4000000000},
        ],
    }
    mock_supabase = _mock_supabase_with_company("MAN_TEST123")

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = admin_client.put("/api/v1/companies/MAN_TEST123/manual", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["corp_code"] == "MAN_TEST123"
    assert data["is_listed"] is False


def test_put_manual_company_not_found(admin_client):
    """존재하지 않는 corp_code PUT → 404"""
    payload = {
        "company_name": "없는회사",
        "financials": [{"bsns_year": "2024", "revenue": 1000000}],
    }
    mock_supabase = _mock_supabase_company_not_found()

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = admin_client.put("/api/v1/companies/MAN_NOTEXIST/manual", json=payload)

    assert response.status_code == 404


def test_put_manual_company_non_admin_forbidden(builder_client):
    """Admin 아닌 사용자 PUT → 403"""
    payload = {
        "company_name": "테스트비상장(주)",
        "financials": [{"bsns_year": "2024", "revenue": 1000000}],
    }
    mock_supabase = _mock_supabase_non_admin()

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase), \
         patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = builder_client.put("/api/v1/companies/MAN_TEST123/manual", json=payload)

    assert response.status_code == 403
