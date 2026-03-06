"""
Story 2.1: 인증(auth.py) 단위 테스트
- get_current_user Dependency를 직접 테스트
- 현재 라우터에 auth 가드 미적용이므로 함수 레벨 테스트 사용
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestGetCurrentUser:
    def test_valid_token_returns_user(self):
        """유효한 토큰 → 사용자 반환"""
        mock_user_obj = MagicMock()
        mock_user_obj.user.id = "test-user-id"
        mock_user_obj.user.email = "test@example.com"

        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.return_value = mock_user_obj

        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            from app.core.auth import get_current_user

            creds = make_credentials("valid-jwt-token")
            user = asyncio.run(get_current_user(creds))

        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        mock_supabase.auth.get_user.assert_called_once_with("valid-jwt-token")

    def test_invalid_token_raises_401(self):
        """유효하지 않은 토큰 → HTTP 401"""
        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT")

        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            from app.core.auth import get_current_user

            creds = make_credentials("invalid-token")
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(get_current_user(creds))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    def test_no_user_in_response_raises_401(self):
        """Supabase가 user=None 반환 → HTTP 401"""
        mock_response = MagicMock()
        mock_response.user = None

        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.return_value = mock_response

        with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
            from app.core.auth import get_current_user

            creds = make_credentials("token-with-no-user")
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(get_current_user(creds))

        assert exc_info.value.status_code == 401

    def test_missing_token_raises_401(self):
        """토큰 없음 → HTTPBearer가 401 반환 (FastAPI 기본 동작)"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, Depends
        from app.core.auth import get_current_user

        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": user.id}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/protected")

        # HTTPBearer는 Authorization 헤더 없으면 401 반환 (FastAPI 0.95+)
        assert response.status_code == 401
