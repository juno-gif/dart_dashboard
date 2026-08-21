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


class TestAuditReportSignHandling:
    """감사보고서(F001) 파싱 경로의 손실 계정 부호·중복 처리 검증
    회귀 배경: NHN페이코(2025년 실제 순손실 -55억)가 대시보드에 순이익 +1366억으로 표시되던 버그
    """

    def _run_sync(self, audit_rows):
        mock_dart = MagicMock()
        mock_dart.finstate.return_value = None  # finstate 실패 → 감사보고서 폴백 유도

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {"audit_only": False}

        captured = []

        def fake_upsert(data, on_conflict):
            captured.extend(data)
            m = MagicMock()
            m.execute.return_value.data = data
            return m

        mock_supabase.table.return_value.upsert.side_effect = fake_upsert

        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            with patch("app.services.dart_client.get_supabase_client", return_value=mock_supabase):
                with patch("app.services.dart_client._get_financial_from_audit_report", return_value=audit_rows):
                    from app.services.dart_client import sync_company_financials
                    sync_company_financials("01206896", years=1)

        return captured

    def test_loss_account_from_audit_report_not_double_negated(self):
        """_parse_amount()가 이미 음수로 변환한 손실 계정 값이 다시 반전되지 않아야 함"""
        captured = self._run_sync([
            {"account_nm": "X. 당기순손실", "thstrm_amount": "-5548248210", "reprt_code": "F001", "fs_div": "CFS"},
        ])

        net_income_rows = [r for r in captured if r.get("account_key") == "net_income"]
        assert len(net_income_rows) == 1
        assert net_income_rows[0]["amount"] == -5548248210

    def test_dedup_prefers_numbered_prefix_over_larger_bare_duplicate(self):
        """번호 접두사 없는 맨몸 계정명이 절댓값이 더 크더라도, 번호 붙은 본표 라인이 우선해야 함"""
        captured = self._run_sync([
            {"account_nm": "X. 당기순손실", "thstrm_amount": "-5548248210", "reprt_code": "F001", "fs_div": "CFS"},
            {"account_nm": "당기순손실", "thstrm_amount": "-136582748759", "reprt_code": "F001", "fs_div": "CFS"},
        ])

        net_income_rows = [r for r in captured if r.get("account_key") == "net_income"]
        assert len(net_income_rows) == 1
        assert net_income_rows[0]["amount"] == -5548248210

    def test_dedup_still_prefers_larger_amount_when_neither_has_prefix(self):
        """기존 회귀 방지: 둘 다 번호가 없으면 여전히 절댓값이 큰 쪽(영업수익)이 우선해야 함"""
        captured = self._run_sync([
            {"account_nm": "이자수익", "thstrm_amount": "800000000", "reprt_code": "F001", "fs_div": "CFS"},
            {"account_nm": "영업수익", "thstrm_amount": "143200000000", "reprt_code": "F001", "fs_div": "CFS"},
        ])

        revenue_rows = [r for r in captured if r.get("account_key") == "revenue"]
        assert len(revenue_rows) == 1
        assert revenue_rows[0]["amount"] == 143200000000


class TestGetCompanyProfile:
    """get_company_profile() — DART 기업개황(company.json) 테스트"""

    def test_returns_mapped_fields(self):
        mock_dart = MagicMock()
        mock_dart.company.return_value = {
            "status": "000",
            "est_dt": "19690113",
            "ceo_nm": "홍길동",
            "adres": "경기도 수원시",
            "hm_url": "www.example.com",
            "bizr_no": "1248100998",
        }
        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            from app.services.dart_client import get_company_profile
            result = get_company_profile("005930")

        assert result["est_dt"] == "19690113"
        assert result["ceo_nm"] == "홍길동"
        assert result["bizr_no"] == "1248100998"

    def test_returns_empty_dict_on_error_status(self):
        mock_dart = MagicMock()
        mock_dart.company.return_value = {"status": "013", "message": "조회 결과 없음"}
        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            from app.services.dart_client import get_company_profile
            result = get_company_profile("999999")

        assert result == {}

    def test_returns_empty_dict_on_exception(self):
        mock_dart = MagicMock()
        mock_dart.company.side_effect = Exception("network error")
        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            from app.services.dart_client import get_company_profile
            result = get_company_profile("005930")

        assert result == {}


class TestGetEmployeeCount:
    """get_employee_count() — 사업보고서 직원현황 → 국민연금 폴백 체인 테스트"""

    def test_uses_dart_report_when_available(self):
        mock_dart = MagicMock()
        mock_dart.report.return_value = pd.DataFrame([
            {"fo_bbm": "전체", "sexdstn": "남", "sm": "100"},
            {"fo_bbm": "전체", "sexdstn": "여", "sm": "50"},
        ])
        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            from app.services.dart_client import get_employee_count
            count, source = get_employee_count("005930", "삼성전자")

        assert count == 150
        assert source == "dart_report"

    def test_falls_back_to_nps_when_report_empty(self):
        mock_dart = MagicMock()
        mock_dart.report.return_value = pd.DataFrame()

        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            with patch("app.services.dart_client.settings") as mock_settings:
                mock_settings.NPS_API_KEY = "test-key"
                with patch("app.services.dart_client._get_employee_count_from_nps", return_value=42) as mock_nps:
                    from app.services.dart_client import get_employee_count
                    count, source = get_employee_count("MAN_ABC", "테스트법인")

        mock_nps.assert_called_once_with("테스트법인")
        assert count == 42
        assert source == "nps"

    def test_returns_none_when_both_sources_fail(self):
        mock_dart = MagicMock()
        mock_dart.report.return_value = pd.DataFrame()

        with patch("app.services.dart_client.OpenDartReader", return_value=mock_dart):
            with patch("app.services.dart_client._get_employee_count_from_nps", return_value=None):
                from app.services.dart_client import get_employee_count
                count, source = get_employee_count("MAN_ABC", "테스트법인")

        assert count is None
        assert source is None


class TestNpsFallback:
    """_get_employee_count_from_nps() — 국민연금 사업장 가입자 현황 조회 테스트"""

    def test_returns_none_without_api_key(self):
        with patch("app.services.dart_client.settings") as mock_settings:
            mock_settings.NPS_API_KEY = ""
            from app.services.dart_client import _get_employee_count_from_nps
            assert _get_employee_count_from_nps("테스트법인") is None

    def test_matches_by_name_and_returns_member_count(self):
        search_xml = (
            "<response><body><items>"
            "<item><wkplNm>테스트법인</wkplNm><wkplJnngStcd>1</wkplJnngStcd><seq>999</seq></item>"
            "</items></body></response>"
        ).encode("utf-8")
        detail_xml = "<response><body><item><jnngpCnt>42</jnngpCnt></item></body></response>".encode("utf-8")

        mock_search_resp = MagicMock(content=search_xml)
        mock_detail_resp = MagicMock(content=detail_xml)

        with patch("app.services.dart_client.settings") as mock_settings:
            mock_settings.NPS_API_KEY = "test-key"
            with patch("app.services.dart_client.requests.get", side_effect=[mock_search_resp, mock_detail_resp]):
                from app.services.dart_client import _get_employee_count_from_nps
                result = _get_employee_count_from_nps("테스트법인")

        assert result == 42

    def test_returns_none_when_no_name_match(self):
        search_xml = (
            "<response><body><items>"
            "<item><wkplNm>전혀다른회사</wkplNm><wkplJnngStcd>1</wkplJnngStcd><seq>999</seq></item>"
            "</items></body></response>"
        ).encode("utf-8")
        mock_search_resp = MagicMock(content=search_xml)

        with patch("app.services.dart_client.settings") as mock_settings:
            mock_settings.NPS_API_KEY = "test-key"
            with patch("app.services.dart_client.requests.get", return_value=mock_search_resp):
                from app.services.dart_client import _get_employee_count_from_nps
                result = _get_employee_count_from_nps("테스트법인")

        assert result is None


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
