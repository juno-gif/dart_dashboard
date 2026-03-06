"""
DART 장애 graceful 처리 테스트 — Story 1.6
DART 장애 시 503 + DART_API_UNAVAILABLE 반환 및 DB 캐시 폴백 검증
"""
import logging
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


def _make_fin_rows(years=2, corp_code="005930"):
    """테스트용 financial_statements 행 생성"""
    rows = []
    for year_offset in range(years):
        bsns_year = str(2024 - year_offset)
        for key in ["revenue", "operating_profit", "net_income"]:
            rows.append({
                "id": f"{bsns_year}-{key}",
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


def test_dart_sync_failure_returns_503_when_db_empty(client):
    """DART 장애 + DB 빈 경우 → 503 + DART_API_UNAVAILABLE 반환"""
    mock_supabase = _make_supabase_mock([])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch(
            "app.services.financial_service.sync_company_financials",
            side_effect=Exception("DART down"),
        ):
            response = client.get("/api/v1/companies/005930/financials?type=pl")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["error"] == "DART_API_UNAVAILABLE"
    assert body["detail"]["status_code"] == 503


def test_dart_sync_failure_returns_cached_when_db_has_data(client):
    """DART 장애여도 DB에 데이터 있으면 정상 반환 (sync 호출 안 됨)"""
    rows = _make_fin_rows(years=2)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials") as mock_sync:
            response = client.get("/api/v1/companies/005930/financials?type=pl")

    assert response.status_code == 200
    mock_sync.assert_not_called()  # DB에 데이터 있으면 sync 안 함


def test_dart_sync_failure_compare_returns_503(client):
    """compare 엔드포인트: DART 장애 + DB 빈 경우 → 503 + DART_API_UNAVAILABLE"""
    mock_supabase = _make_supabase_mock([])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch(
            "app.services.financial_service.sync_company_financials",
            side_effect=Exception("DART down"),
        ):
            response = client.get("/api/v1/companies/compare?codes=005930,035720&type=pl")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["error"] == "DART_API_UNAVAILABLE"


def test_dart_failure_logs_warning(caplog):
    """DART 장애 시 warning 로그 기록 확인"""
    from app.services.financial_service import get_pl_data

    mock_supabase = _make_supabase_mock([])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch(
            "app.services.financial_service.sync_company_financials",
            side_effect=Exception("DART API timeout"),
        ):
            with caplog.at_level(logging.WARNING, logger="app.services.financial_service"):
                with pytest.raises(Exception):
                    get_pl_data("005930", years=5)

    assert any("DART sync failed" in r.message for r in caplog.records)
    assert any("005930" in r.message for r in caplog.records)


def test_unmapped_account_logs_warning(caplog):
    """미매핑 계정과목 수신 시 warning 로그 기록 확인"""
    from app.services.dart_client import sync_company_financials

    mock_supabase = MagicMock()
    # account_mappings: 빈 매핑 반환 (미매핑 시나리오)
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = []

    # DART finstate에서 알 수 없는 계정명 반환
    mock_dart_rows = [
        {
            "account_nm": "알수없는계정과목",
            "thstrm_amount": "1000000",
            "reprt_code": "11011",
            "fs_div": "CFS",
        }
    ]

    with patch("app.services.dart_client.get_supabase_client", return_value=mock_supabase):
        with patch(
            "app.services.dart_client.get_financial_statements",
            return_value=mock_dart_rows,
        ):
            # upsert도 mock
            mock_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock()
            with caplog.at_level(logging.WARNING, logger="app.services.dart_client"):
                sync_company_financials("005930", years=1)

    assert any("Unmapped account" in r.message for r in caplog.records)
    assert any("알수없는계정과목" in r.message for r in caplog.records)
