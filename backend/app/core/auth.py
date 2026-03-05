"""
JWT 검증 미들웨어 (Supabase SDK 방식)
완전 구현: Story 2.1 (Magic Link 인증 설정)
[Source: architecture.md - Authentication & Security]
"""

# TODO: Story 2.1에서 구현
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from app.core.database import supabase_client

# bearer_scheme = HTTPBearer()

# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
#     token = credentials.credentials
#     try:
#         user = supabase_client.auth.get_user(token)
#         return user
#     except Exception:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
