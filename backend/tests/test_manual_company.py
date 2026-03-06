"""
비상장사 수기 입력 테스트 — Story 5.1
POST /api/v1/companies/manual (인증 필요)
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user

MOCK_USER = type("User", (), {"id": "user-123"})()


@pytest.fixture
def client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mock_supabase_empty():
    """기존 비상장사 없는 상태 mock"""
    m = MagicMock()
    # companies 조회 → 없음 (신규 생성 경로)
    m.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    m.table.return_value.insert.return_value.execute.return_value.data = [{}]
    m.table.return_value.upsert.return_value.execute.return_value.data = [{}]
    return m


def test_post_manual_company_success(client):
    """유효한 요청 → 201, Company 반환"""
    payload = {
        "company_name": "테스트비상장(주)",
        "financials": [
            {
                "bsns_year": "2024",
                "revenue": 50000000000,
                "operating_profit": 5000000000,
                "net_income": 3000000000,
            }
        ],
    }
    mock_supabase = _mock_supabase_empty()

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        response = client.post("/api/v1/companies/manual", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "테스트비상장(주)"
    assert data["is_listed"] is False
    assert data["stock_code"] is None
    assert data["corp_code"].startswith("MAN_")


def test_post_manual_company_multiple_years(client):
    """3개 연도 입력 → 201, financial_statements 9개 rows (3 × 3계정)"""
    payload = {
        "company_name": "다연도비상장(주)",
        "financials": [
            {"bsns_year": "2022", "revenue": 10000000000, "operating_profit": 1000000000, "net_income": 700000000},
            {"bsns_year": "2023", "revenue": 12000000000, "operating_profit": 1200000000, "net_income": 900000000},
            {"bsns_year": "2024", "revenue": 15000000000, "operating_profit": 1500000000, "net_income": 1100000000},
        ],
    }
    mock_supabase = _mock_supabase_empty()
    upsert_call_rows = []

    def capture_upsert(rows, **kwargs):
        upsert_call_rows.extend(rows)
        m = MagicMock()
        m.execute.return_value.data = [{}]
        return m

    mock_supabase.table.return_value.upsert.side_effect = capture_upsert

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        response = client.post("/api/v1/companies/manual", json=payload)

    assert response.status_code == 201
    # 3개 연도 × 3계정 = 9 rows
    assert len(upsert_call_rows) == 9
    account_keys = {r["account_key"] for r in upsert_call_rows}
    assert account_keys == {"revenue", "operating_profit", "net_income"}


def test_post_manual_company_auth_required():
    """인증 없이 요청 → 401"""
    from app.main import app
    client_no_auth = TestClient(app)

    payload = {
        "company_name": "미인증테스트",
        "financials": [{"bsns_year": "2024", "revenue": 1000000}],
    }
    response = client_no_auth.post("/api/v1/companies/manual", json=payload)
    assert response.status_code == 401


def test_post_manual_company_reuses_existing(client):
    """동일 company_name 비상장사 이미 존재 → 기존 corp_code 재사용"""
    payload = {
        "company_name": "기존비상장(주)",
        "financials": [{"bsns_year": "2024", "revenue": 5000000000}],
    }
    mock_supabase = MagicMock()
    # 기존 회사 존재 mock
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"corp_code": "MAN_EXISTING"}
    ]
    mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = [{}]

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        response = client.post("/api/v1/companies/manual", json=payload)

    assert response.status_code == 201
    assert response.json()["corp_code"] == "MAN_EXISTING"
