"""
financials.py compare 엔드포인트 테스트 — Story 1.5
GET /api/v1/companies/compare?codes=...&type=pl 검증 (mock 사용)
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _mock_user():
    user = MagicMock()
    user.id = "test-user-id"
    return user


@pytest.fixture
def client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_fin_rows(corp_code: str, years: int = 2):
    """테스트용 financial_statements 행 생성"""
    account_keys = ["revenue", "operating_profit", "net_income"]
    rows = []
    for year_offset in range(years):
        bsns_year = str(2024 - year_offset)
        for key in account_keys:
            rows.append({
                "id": f"{corp_code}-{bsns_year}-{key}",
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": "11011",
                "fs_div": "CFS",
                "account_key": key,
                "account_nm": key,
                "amount": 100000000,
                "synced_at": "2026-01-01T00:00:00Z",
            })
    return rows


def _make_supabase_mock_multi(data_list: list[list]):
    """여러 번 execute() 호출에 순서대로 data 반환하는 mock"""
    mock = MagicMock()
    execute_mock = (
        mock.table.return_value
        .select.return_value
        .eq.return_value
        .in_.return_value
        .order.return_value
        .limit.return_value
        .execute
    )
    execute_mock.side_effect = [MagicMock(data=d) for d in data_list]
    return mock


def test_compare_returns_merged_data(client):
    """두 기업 codes 요청 시 merge된 데이터 반환"""
    rows_a = _make_fin_rows("005930", years=2)
    rows_b = _make_fin_rows("035720", years=2)

    mock_supabase = _make_supabase_mock_multi([rows_a, rows_b])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/companies/compare?codes=005930,035720&type=pl")

    assert response.status_code == 200
    result = response.json()
    assert len(result) == len(rows_a) + len(rows_b)
    corp_codes = {r["corp_code"] for r in result}
    assert "005930" in corp_codes
    assert "035720" in corp_codes


def test_compare_single_code_allowed(client):
    """codes=1개도 허용 (1~5개 범위)"""
    rows = _make_fin_rows("005930", years=1)
    mock_supabase = _make_supabase_mock_multi([rows])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/companies/compare?codes=005930&type=pl")

    assert response.status_code == 200


def test_compare_rejects_more_than_5_codes(client):
    """6개 이상 codes 요청 시 400 반환"""
    codes = ",".join(["000001"] * 6)
    response = client.get(f"/api/v1/companies/compare?codes={codes}&type=pl")
    assert response.status_code == 400


def test_compare_rejects_empty_codes(client):
    """빈 codes 요청 시 400 반환"""
    response = client.get("/api/v1/companies/compare?codes=&type=pl")
    assert response.status_code == 400


def test_compare_rejects_invalid_type(client):
    """type=invalid 요청 시 400 반환 (pl, bs, cf만 지원)"""
    response = client.get("/api/v1/companies/compare?codes=005930&type=invalid")
    assert response.status_code == 400


def test_compare_rejects_invalid_years(client):
    """years 범위 초과 시 400 반환"""
    response = client.get("/api/v1/companies/compare?codes=005930&years=0&type=pl")
    assert response.status_code == 400
    response2 = client.get("/api/v1/companies/compare?codes=005930&years=11&type=pl")
    assert response2.status_code == 400


def test_compare_does_not_conflict_with_single_financials(client):
    """GET /companies/compare 가 /companies/{corp_code}/financials 와 경로 충돌 없음"""
    rows = _make_fin_rows("005930", years=1)
    mock_supabase = _make_supabase_mock_multi([rows])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        # compare 엔드포인트: corp_code="compare"로 매칭되지 않아야 함
        compare_response = client.get("/api/v1/companies/compare?codes=005930&type=pl")
    assert compare_response.status_code == 200
