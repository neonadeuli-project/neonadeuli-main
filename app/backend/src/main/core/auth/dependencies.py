from asyncio.log import logger
from typing import Tuple
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

from src.main.core.auth.jwt import verify_token
from src.main.core.exceptions import AuthenticationError
from src.main.domains.user.repository.user_repository import UserRepository
from src.main.domains.user.dependencies import get_redis_token_manager
from src.main.domains.user.models.user import User
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.db.deps import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db),
    token_manager: TokenRepository = Depends(get_redis_token_manager)
) -> Tuple[User, str]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate":"Bearer"},
    )

    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("제공된 토큰이 없습니다.")

    try:
        is_blacklisted = await token_manager.is_token_blacklisted(token)
        logger.info(f"토큰 블랙리스트 결과 검사: {is_blacklisted}")
        if is_blacklisted:
            logger.error("토큰이 블랙리스트에 있습니다.")
            raise credentials_exception
        
        payload = verify_token(token)
        logger.info(f"토큰 페이로드: {payload}")
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT 에러 발생: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"토큰 인증 에러 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"토큰 검증 중 오류 발생: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_repository = UserRepository(db)
    try:
        user = await user_repository.get_by_email(user_email)
        logger.info(f"유저 검색 결과: {user}")
        if user is None:
            logger.error(f"{user_email} 이메일 해당 유저 없음")
            raise credentials_exception
    except Exception as e:
        logger.error(f"유저 검색 에러 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 조회 중 오류 발생: {str(e)}"
        )
    
    return user, token