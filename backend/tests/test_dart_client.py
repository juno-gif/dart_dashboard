"""
dart_client.py 테스트 — Story 1.2
DART API 격리 모듈 검증 (mock 사용)
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def reset_dart_singleton():
    """각 테스트 전 _dart 싱글턴 리셋"""
    import app.services.dart_client as dc
    dc._dart = None
    yield
    dc._dart = None


def test_search_companies_returns_list():
    """search_companies()가 리스트를 반환하는지 검증"""
    mock_dart = MagicMock()
    mock_dart.corp_codes = pd.DataFrame([
        {"corp_code": "005930", "corp_name": "삼성전자", "stock_code": "005930"},
        {"corp_code": "035720", "corp_name": "카카오", "stock_code": "035720"},
    ])

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        from app.services.dart_client import search_companies
        result = search_companies("삼성")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["corp_code"] == "005930"


def test_search_companies_empty_on_no_match():
    """매칭 결과 없을 때 빈 리스트 반환"""
    mock_dart = MagicMock()
    mock_dart.corp_codes = pd.DataFrame([
        {"corp_code": "005930", "corp_name": "삼성전자", "stock_code": "005930"},
    ])

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        from app.services.dart_client import search_companies
        result = search_companies("존재하지않는기업XYZ")

    assert result == []


def test_search_companies_max_8_results():
    """최대 8건만 반환하는지 검증"""
    mock_dart = MagicMock()
    mock_dart.corp_codes = pd.DataFrame([
        {"corp_code": f"00000{i}", "corp_name": f"삼성테스트{i}", "stock_code": f"0000{i}"}
        for i in range(20)
    ])

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        from app.services.dart_client import search_companies
        result = search_companies("삼성테스트")

    assert len(result) <= 8


def test_get_financial_statements_returns_list():
    """get_financial_statements()가 리스트를 반환하는지 검증"""
    mock_dart = MagicMock()
    mock_dart.finstate.return_value = pd.DataFrame([
        {
            "reprt_code": "11011",
            "fs_div": "CFS",
            "account_nm": "매출액",
            "thstrm_amount": "100,000",
        }
    ])

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        from app.services.dart_client import get_financial_statements
        result = get_financial_statements("005930", "2024")

    assert isinstance(result, list)
    assert len(result) == 1


def test_get_financial_statements_empty_on_none():
    """DART API가 None 반환 시 빈 리스트 반환"""
    mock_dart = MagicMock()
    mock_dart.finstate.return_value = None

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        from app.services.dart_client import get_financial_statements
        result = get_financial_statements("005930", "2024")

    assert result == []


def test_sync_company_financials_returns_dict():
    """sync_company_financials()가 synced_rows를 포함한 dict 반환"""
    mock_dart = MagicMock()
    mock_dart.finstate.return_value = pd.DataFrame([
        {
            "reprt_code": "11011",
            "fs_div": "CFS",
            "account_nm": "매출액",
            "thstrm_amount": "100000",
        }
    ])

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
        {"account_nm": "매출액", "account_key": "revenue"}
    ]
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock()

    with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
        with patch("app.services.dart_client.get_supabase_client", return_value=mock_supabase):
            from app.services.dart_client import sync_company_financials
            result = sync_company_financials("005930", years=1)

    assert result["corp_code"] == "005930"
    assert "synced_rows" in result


class TestSyncAllCompanies:
    """Story 3.3: sync_all_companies() 테스트"""

    def test_sync_all_companies_success(self, caplog):
        """2개 기업 성공 동기화 + 완료 로그 검증"""
        import logging
        mock_sb = MagicMock()
        # companies 테이블 조회 → 2개 기업
        mock_sb.table.return_value.select.return_value.execute.return_value.data = [
            {"corp_code": "000001"},
            {"corp_code": "000002"},
        ]
        # financial_statements bsns_year 조회 (before/after) — 신규 없음
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with patch("app.services.dart_client.sync_company_financials", return_value={"synced_rows": 10}):
                with caplog.at_level(logging.INFO, logger="app.services.dart_client"):
                    from app.services.dart_client import sync_all_companies
                    result = sync_all_companies()

        assert result["companies_synced"] == 2
        assert result["records_synced"] == 20
        assert "[DART_SYNC] 완료: 2개 기업, 20개 레코드 갱신" in caplog.text

    def test_sync_all_companies_partial_failure(self, caplog):
        """1개 기업 실패해도 나머지 계속 진행 + 에러 로그 검증"""
        import logging
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.return_value.data = [
            {"corp_code": "000001"},
            {"corp_code": "000002"},
        ]
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        def mock_sync(corp_code, years=5):
            if corp_code == "000001":
                raise Exception("DART API timeout")
            return {"synced_rows": 5}

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with patch("app.services.dart_client.sync_company_financials", side_effect=mock_sync):
                with caplog.at_level(logging.ERROR, logger="app.services.dart_client"):
                    from app.services.dart_client import sync_all_companies
                    result = sync_all_companies()

        assert result["companies_synced"] == 1  # 성공한 기업만 카운트
        assert "[DART_SYNC] 실패: 000001" in caplog.text

    def test_sync_all_companies_rate_limit(self, caplog):
        """18,000건 초과 시 조기 종료 + 경고 로그"""
        import logging
        mock_sb = MagicMock()
        # 4,000개 기업 (5 calls × 3,601번째 = 18,005 → 3,601번째에서 멈춤)
        mock_sb.table.return_value.select.return_value.execute.return_value.data = [
            {"corp_code": f"{i:06d}"} for i in range(4000)
        ]
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with patch("app.services.dart_client.sync_company_financials", return_value={"synced_rows": 1}):
                with caplog.at_level(logging.WARNING, logger="app.services.dart_client"):
                    from app.services.dart_client import sync_all_companies
                    result = sync_all_companies()

        assert "[DART_SYNC] 한도 초과 방지: 조기 종료" in caplog.text
        # 4,000개 전부 처리되지 않아야 함 (18,000 / 5 = 3,600개까지만)
        assert result["companies_synced"] <= 3600

    def test_sync_all_companies_new_data_detected(self):
        """신규 bsns_year 감지 시 companies.last_new_data_at 업데이트"""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.return_value.data = [
            {"corp_code": "005930"},
        ]

        # before: 2022, 2023만 있음
        before_result = MagicMock(data=[{"bsns_year": "2022"}, {"bsns_year": "2023"}])
        # after: 2024 추가
        after_result = MagicMock(data=[{"bsns_year": "2022"}, {"bsns_year": "2023"}, {"bsns_year": "2024"}])

        mock_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            before_result,
            after_result,
        ]

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with patch("app.services.dart_client.sync_company_financials", return_value={"synced_rows": 3}):
                from app.services.dart_client import sync_all_companies
                sync_all_companies()

        # last_new_data_at 업데이트 호출 확인
        mock_sb.table.return_value.update.assert_called_once()
        update_call_args = mock_sb.table.return_value.update.call_args[0][0]
        assert "last_new_data_at" in update_call_args

    def test_sync_all_companies_no_companies(self, caplog):
        """companies 테이블 비어있으면 완료: 0개 기업 로그"""
        import logging
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.return_value.data = []

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with caplog.at_level(logging.INFO, logger="app.services.dart_client"):
                from app.services.dart_client import sync_all_companies
                result = sync_all_companies()

        assert result["companies_synced"] == 0
        assert result["records_synced"] == 0
        assert "[DART_SYNC] 완료: 0개 기업, 0개 레코드 갱신" in caplog.text

    def test_sync_all_companies_db_error_on_list(self, caplog):
        """기업 목록 조회 DB 오류 시 즉시 종료"""
        import logging
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.side_effect = Exception("DB connection error")

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with caplog.at_level(logging.ERROR, logger="app.services.dart_client"):
                from app.services.dart_client import sync_all_companies
                result = sync_all_companies()

        assert result == {"companies_synced": 0, "records_synced": 0}
        assert "[DART_SYNC] 기업 목록 조회 실패" in caplog.text


def test_dart_client_is_only_importer():
    """OpenDartReader가 dart_client.py에서만 import되는지 확인 (다른 모듈에 없는지)"""
    import ast
    import os

    backend_root = os.path.join(os.path.dirname(__file__), "..", "app")
    violations = []

    for dirpath, _, filenames in os.walk(backend_root):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, filename)
            # dart_client.py는 제외
            if filepath.endswith("dart_client.py"):
                continue
            with open(filepath) as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = (
                        [alias.name for alias in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module or ""]
                    )
                    if any("OpenDartReader" in (n or "") for n in names):
                        violations.append(filepath)

    assert violations == [], f"OpenDartReader가 dart_client.py 외에서 import됨: {violations}"
