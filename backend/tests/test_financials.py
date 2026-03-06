"""
financials.py + financial_service.py 테스트 — Story 1.4
GET /api/v1/companies/{corp_code}/financials DB-First 로직 검증 (mock 사용)
"""
from unittest.mock import MagicMock, call, patch

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


def _make_fin_rows(years=2, account_keys=None, fs_div="CFS"):
    """테스트용 financial_statements 행 생성"""
    if account_keys is None:
        account_keys = ["revenue", "operating_profit", "net_income"]
    rows = []
    for year_offset in range(years):
        bsns_year = str(2024 - year_offset)
        for key in account_keys:
            rows.append({
                "id": f"{bsns_year}-{key}",
                "corp_code": "005930",
                "bsns_year": bsns_year,
                "reprt_code": "11011",
                "fs_div": fs_div,
                "account_key": key,
                "account_nm": key,
                "amount": 100000000,
                "synced_at": "2026-01-01T00:00:00Z",
            })
    return rows


def _make_supabase_mock(data: list):
    """Supabase 체인 mock 생성 (financial_statements 조회용)"""
    mock = MagicMock()
    (
        mock.table.return_value
        .select.return_value
        .eq.return_value
        .in_.return_value
        .order.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = data
    return mock


def test_get_financials_returns_db_data_when_cached(client):
    """DB에 데이터 있을 때 DART sync 없이 DB 데이터 반환"""
    rows = _make_fin_rows(years=2)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials") as mock_sync:
            response = client.get("/api/v1/companies/005930/financials?years=5&type=pl")

    assert response.status_code == 200
    assert len(response.json()) > 0
    mock_sync.assert_not_called()


def test_get_financials_syncs_dart_when_db_empty(client):
    """DB 빈 경우 DART sync 호출 후 재조회"""
    rows = _make_fin_rows(years=1)
    mock_supabase = MagicMock()
    execute_mock = mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.order.return_value.limit.return_value.execute

    # 첫 조회: 빈 결과, 두 번째 조회: 데이터 반환
    execute_mock.side_effect = [
        MagicMock(data=[]),
        MagicMock(data=rows),
    ]

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials") as mock_sync:
            response = client.get("/api/v1/companies/005930/financials?type=pl")

    assert response.status_code == 200
    mock_sync.assert_called_once_with("005930", years=5)


def test_get_financials_bs_returns_db_data(client):
    """type=bs 요청 시 BS 데이터 반환"""
    bs_keys = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]
    rows = _make_fin_rows(years=2, account_keys=bs_keys)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials"):
            response = client.get("/api/v1/companies/005930/financials?years=3&type=bs")

    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert all(r["account_key"] in bs_keys for r in result)


def test_get_financials_cf_returns_db_data(client):
    """type=cf 요청 시 CF 데이터 반환"""
    cf_keys = ["operating_cf", "investing_cf", "financing_cf"]
    rows = _make_fin_rows(years=2, account_keys=cf_keys)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials"):
            response = client.get("/api/v1/companies/005930/financials?years=3&type=cf")

    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert all(r["account_key"] in cf_keys for r in result)


def test_get_financials_rejects_invalid_type(client):
    """type=invalid 요청 시 400 반환"""
    response = client.get("/api/v1/companies/005930/financials?type=invalid")
    assert response.status_code == 400


def test_get_financials_rejects_invalid_years(client):
    """years 범위 초과 시 400 반환"""
    response = client.get("/api/v1/companies/005930/financials?years=0&type=pl")
    assert response.status_code == 400
    response2 = client.get("/api/v1/companies/005930/financials?years=11&type=pl")
    assert response2.status_code == 400


def test_prefer_cfs_over_ofs():
    """CFS 우선 선택 로직 검증"""
    from app.services.financial_service import _prefer_cfs

    rows = [
        {"bsns_year": "2024", "account_key": "revenue", "fs_div": "OFS", "amount": 100},
        {"bsns_year": "2024", "account_key": "revenue", "fs_div": "CFS", "amount": 200},
    ]
    result = _prefer_cfs(rows, years=5)
    assert len(result) == 1
    assert result[0]["fs_div"] == "CFS"
    assert result[0]["amount"] == 200


def test_prefer_cfs_limits_years():
    """최근 N연도만 반환 검증"""
    from app.services.financial_service import _prefer_cfs

    rows = []
    for y in range(2020, 2026):  # 6개 연도
        rows.append({"bsns_year": str(y), "account_key": "revenue", "fs_div": "CFS", "amount": y})

    result = _prefer_cfs(rows, years=3)
    years_in_result = {r["bsns_year"] for r in result}
    assert len(years_in_result) <= 3
    assert "2025" in years_in_result  # 최신 연도 포함
