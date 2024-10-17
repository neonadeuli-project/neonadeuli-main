from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.main.domains.user.dependencies import get_redis_token_manager, get_user_service
from src.main.core.auth.dependencies import get_current_user, oauth2_scheme
from src.main.db.deps import get_db
from src.main.db.database import redis_client

security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    if request.url.path == "/api/v1/users/token/refresh":
        return await call_next(request)
    try:
        # DB 세션 획득
        db = await get_db().__anext__()
        token_manager = get_redis_token_manager()

        auth: HTTPAuthorizationCredentials = await security(request)
        if auth:
            token = auth.credentials
        else:
            # Authorization 헤더에 토큰이 없으면 쿠키에서 찾습니다.
            token = request.cookies.get("access_token")
        
        if token:
            try:
                user = await get_current_user(token, db, token_manager)
                request.state.user = user
            except HTTPException:
                request.state.user = None
        else:
            request.state.user = None
    except Exception as e:
        print(f"인증 미들웨어 에러: {str(e)}")
        request.state.user = None

    response = await call_next(request)
    return response