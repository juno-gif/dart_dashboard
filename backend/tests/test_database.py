"""
database.py 테스트 — Story 1.2
Supabase 클라이언트 초기화 및 싱글턴 패턴 검증
"""
from unittest.mock import MagicMock, patch


def test_get_supabase_client_returns_client():
    """get_supabase_client()가 Client 객체를 반환하는지 검증"""
    mock_client = MagicMock()
    with patch("app.core.database.create_client", return_value=mock_client) as mock_create:
        # 싱글턴 초기화를 위해 _supabase_client 리셋
        import app.core.database as db_module
        db_module._supabase_client = None

        from app.core.database import get_supabase_client
        client = get_supabase_client()

        assert client is mock_client
        mock_create.assert_called_once()


def test_get_supabase_client_singleton():
    """동일한 클라이언트 인스턴스를 반환하는지 검증 (싱글턴)"""
    mock_client = MagicMock()
    with patch("app.core.database.create_client", return_value=mock_client):
        import app.core.database as db_module
        db_module._supabase_client = None

        from app.core.database import get_supabase_client
        client1 = get_supabase_client()
        client2 = get_supabase_client()

        assert client1 is client2


def test_get_supabase_client_uses_service_key():
    """Service Key (SUPABASE_SERVICE_KEY)로 초기화되는지 검증"""
    mock_client = MagicMock()
    with patch("app.core.database.create_client", return_value=mock_client) as mock_create:
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.SUPABASE_URL = "https://test.supabase.co"
            mock_settings.SUPABASE_SERVICE_KEY = "service-key-secret"

            import app.core.database as db_module
            db_module._supabase_client = None

            from app.core.database import get_supabase_client
            get_supabase_client()

            args = mock_create.call_args
            assert args[0][1] == "service-key-secret"
