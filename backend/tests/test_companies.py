"""
companies.py 테스트 — Story 1.3, 3.3
GET /api/v1/companies/search DB-First 로직 검증 (mock 사용)
Story 3.3: GET /api/v1/companies/new-data-status 테스트
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


def _make_supabase_mock(data: list):
    """Supabase 체인 mock 생성 헬퍼"""
    mock_supabase = MagicMock()
    (
        mock_supabase.table.return_value
        .select.return_value
        .or_.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = data
    return mock_supabase


def test_search_returns_db_results_when_found(client):
    """DB에 결과 있을 때 DART API 호출 없이 DB 결과 반환"""
    db_data = [
        {"corp_code": "005930", "company_name": "삼성전자", "stock_code": "005930", "is_listed": True}
    ]
    mock_supabase = _make_supabase_mock(db_data)

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.companies.dart_search_companies") as mock_dart:
            response = client.get("/api/v1/companies/search?q=삼성전자")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["corp_code"] == "005930"
    mock_dart.assert_not_called()


def test_search_falls_back_to_dart_when_db_empty(client):
    """DB 결과 없을 때 DART API 호출"""
    mock_supabase = _make_supabase_mock([])
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock()

    dart_data = [
        {"corp_code": "035720", "corp_name": "카카오", "stock_code": "035720"}
    ]

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.companies.dart_search_companies", return_value=dart_data):
            response = client.get("/api/v1/companies/search?q=카카오")

    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["company_name"] == "카카오"


def test_search_returns_empty_when_no_results(client):
    """DB 없고 DART도 없을 때 빈 배열 반환"""
    mock_supabase = _make_supabase_mock([])

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.companies.dart_search_companies", return_value=[]):
            response = client.get("/api/v1/companies/search?q=존재하지않는기업XYZ")

    assert response.status_code == 200
    assert response.json() == []


def test_search_requires_q_param(client):
    """q 파라미터 없을 때 422 반환"""
    response = client.get("/api/v1/companies/search")
    assert response.status_code == 422


def test_search_limit_respected(client):
    """limit 파라미터 적용 확인"""
    db_data = [
        {"corp_code": f"00000{i}", "company_name": f"테스트{i}", "stock_code": None, "is_listed": False}
        for i in range(3)
    ]
    mock_supabase = _make_supabase_mock(db_data)

    with patch("app.api.v1.companies.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/companies/search?q=테스트&limit=3")

    assert response.status_code == 200
    assert len(response.json()) <= 3


class TestNewDataStatus:
    """Story 3.3: GET /api/v1/companies/new-data-status 테스트"""

    def test_new_data_status_returns_recent_companies(self, client):
        """7일 내 last_new_data_at 있는 기업 반환"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.return_value.data = [
            {"corp_code": "005930"}
        ]

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            response = client.get("/api/v1/companies/new-data-status?codes=005930,035720")

        assert response.status_code == 200
        assert response.json() == {"new_data_codes": ["005930"]}

    def test_new_data_status_empty_when_no_new_data(self, client):
        """신규 데이터 없으면 빈 배열 반환"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.return_value.data = []

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            response = client.get("/api/v1/companies/new-data-status?codes=005930")

        assert response.status_code == 200
        assert response.json() == {"new_data_codes": []}

    def test_new_data_status_empty_codes_returns_empty(self, client):
        """빈 codes 파라미터 시 빈 배열 반환 (DB 조회 없음)"""
        mock_sb = MagicMock()

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            response = client.get("/api/v1/companies/new-data-status?codes=")

        assert response.status_code == 200
        assert response.json() == {"new_data_codes": []}
        mock_sb.table.assert_not_called()

    def test_new_data_status_db_error_returns_empty(self, client):
        """DB 오류 시 빈 배열 반환 (비치명적)"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.side_effect = Exception("DB error")

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            response = client.get("/api/v1/companies/new-data-status?codes=005930")

        assert response.status_code == 200
        assert response.json() == {"new_data_codes": []}

    def test_new_data_status_requires_auth_401(self):
        """인증 없으면 401 반환"""
        from app.main import app
        unauthenticated_client = TestClient(app)  # override 없는 클라이언트
        response = unauthenticated_client.get("/api/v1/companies/new-data-status?codes=005930")
        assert response.status_code == 401


class TestCompanyProfile:
    """GET /api/v1/companies/{corp_code}/profile — 기업 개요 지연 로딩 테스트"""

    def _mock_supabase_for_row(self, row: dict):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [row]
        return mock_sb

    def test_returns_cached_profile_when_fresh(self, client):
        """profile_synced_at이 최근이면 DART 재조회 없이 캐시된 값 반환"""
        row = {
            "corp_code": "005930",
            "company_name": "삼성전자",
            "est_dt": "19690113",
            "ceo_nm": "홍길동",
            "adres": "경기도 수원시",
            "hm_url": "www.samsung.com",
            "employee_count": 120000,
            "employee_count_source": "dart_report",
            "profile_synced_at": "2026-08-01T00:00:00",
        }
        mock_sb = self._mock_supabase_for_row(row)

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            with patch("app.api.v1.companies.dart_client.get_company_profile") as mock_profile:
                response = client.get("/api/v1/companies/005930/profile")

        mock_profile.assert_not_called()
        assert response.status_code == 200
        body = response.json()
        assert body["ceo_nm"] == "홍길동"
        assert body["employee_count"] == 120000

    def test_fetches_from_dart_when_stale(self, client):
        """캐시 없거나 오래되면 DART 기업개황 + 임직원수 재조회 후 DB 갱신"""
        row = {
            "corp_code": "005930",
            "company_name": "삼성전자",
            "est_dt": None,
            "ceo_nm": None,
            "adres": None,
            "hm_url": None,
            "employee_count": None,
            "employee_count_source": None,
            "profile_synced_at": None,
        }
        mock_sb = self._mock_supabase_for_row(row)

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            with patch(
                "app.api.v1.companies.dart_client.get_company_profile",
                return_value={"est_dt": "19690113", "ceo_nm": "홍길동", "adres": "경기도", "hm_url": "www.samsung.com", "bizr_no": "1248100998"},
            ):
                with patch(
                    "app.api.v1.companies.dart_client.get_employee_count",
                    return_value=(120000, "dart_report"),
                ):
                    response = client.get("/api/v1/companies/005930/profile")

        assert response.status_code == 200
        body = response.json()
        assert body["ceo_nm"] == "홍길동"
        assert body["employee_count"] == 120000
        assert body["employee_count_source"] == "dart_report"
        mock_sb.table.return_value.update.assert_called_once()

    def test_manual_company_skips_dart(self, client):
        """수기 입력 기업(MAN_ 접두)은 오래된 캐시라도 DART 재조회 안 함"""
        row = {
            "corp_code": "MAN_ABC12345",
            "company_name": "비상장테스트법인",
            "est_dt": None,
            "ceo_nm": None,
            "adres": None,
            "hm_url": None,
            "employee_count": None,
            "employee_count_source": None,
            "profile_synced_at": None,
        }
        mock_sb = self._mock_supabase_for_row(row)

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            with patch("app.api.v1.companies.dart_client.get_company_profile") as mock_profile:
                response = client.get("/api/v1/companies/MAN_ABC12345/profile")

        mock_profile.assert_not_called()
        assert response.status_code == 200
        assert response.json()["employee_count"] is None

    def test_company_not_found_returns_404(self, client):
        """존재하지 않는 corp_code는 404 반환"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            response = client.get("/api/v1/companies/000000/profile")

        assert response.status_code == 404
