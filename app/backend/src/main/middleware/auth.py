from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.main.core.config import settings
from src.main.domains.user.services import UserService


security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = security):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="")
    
async def get_current_user(request: Request, token: dict = verify_token):
    user_service = UserService() # 실제로 의존성 주입 필요


async def auth_middleware(request: Request, call_next):
    try:
        token = await verify_token(request)
        request.state.user = await get_current_user(request, token)
    except HTTPException:
        # 인증 실패 시 처리
        pass

    response = await call_next(request)
    return response