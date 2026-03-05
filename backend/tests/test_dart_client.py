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
