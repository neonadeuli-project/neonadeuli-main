from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from src.main.domains.user.dependencies import get_redis_token_manager
from src.main.core.auth.dependencies import get_current_user, oauth2_scheme
from src.main.db.deps import get_db


security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    try:
        # DB 세션 획득
        db = await get_db().__anext__()
        token_manager = get_redis_token_manager()
        token = await oauth2_scheme(request)
        if token:
            try:
                user = await get_current_user(token, db, token_manager)
                request.state.user = user
            except HTTPException:
                # 인증 실패 시 처리
                request.state.user = None
        else:
            request.state.user = None
    except Exception as e:
        print(f"Auth middleware error: {str(e)}")
        request.state.user = None

    response = await call_next(request)
    return response