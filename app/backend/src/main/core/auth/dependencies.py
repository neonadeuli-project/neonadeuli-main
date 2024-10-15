from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

from src.main.domains.user.dependencies import get_redis_token_manager
from src.main.domains.user.models.user import User
from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.service.user_service import UserService

from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.core.config import settings

from src.main.db.deps import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
        token: str = Depends(oauth2_scheme), 
        db: AsyncSession = Depends(get_db),
        token_manager: TokenRepository = Depends(get_redis_token_manager)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate":"Bearer"},
    )

    if token_manager.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이 토큰은 무효화되었습니다.",
            headers={"WWW-Authenticate":"Bearer"}
        )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user
