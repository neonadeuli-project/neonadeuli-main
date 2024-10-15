from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

from .jwt import verify_token

from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.service.user_service import UserService
from src.main.db.deps import get_db
from src.main.core.exceptions import (
    AuthenticationError
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = verify_token(token)
    email: str = payload.get("sub")
    if email is None:
        raise AuthenticationError("자격 증명을 검증할 수 없습니다.")
    
    user_service = UserService(db)
    user_create = UserCreate(email=email, name="")
    try:
        user = await user_service.get_or_create_user(user_create)
    except Exception as e:
        raise AuthenticationError("유효한 유저를 찾을 수 없습니다.")
    
    return user
