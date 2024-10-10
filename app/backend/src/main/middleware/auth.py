from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from src.main.core.auth.dependencies import get_current_user
from src.main.core.auth.jwt import verify_token
from src.main.db.deps import get_db
from src.main.core.config import settings
from src.main.domains.user.services import UserService


security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    try:
        # DB 세션 획득
        db = await get_db().__anext__()
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            user = await get_current_user(token, db)
            request.state.user = user
        else:
            request.state.user = None
    except HTTPException:
        # 인증 실패 시 처리
        request.state.user = None

    response = await call_next(request)
    return response