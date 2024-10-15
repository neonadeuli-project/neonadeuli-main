from datetime import timedelta

from src.main.domains.user.schemas.auth import RefreshTokenResponse
from src.main.domains.user.service.user_service import UserService
from src.main.core.exceptions import AuthenticationError, NotFoundError
from src.main.core.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)
from src.main.core.auth.token_manager import RedisTokenManager
from src.main.core.config import settings

class AuthService:
    def __init__(self, user_service: UserService, token_manager: RedisTokenManager):
        self.user_service = user_service
        self.token_manager = token_manager

    async def refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("유효하지 않은 Refresh Token입니다.")
            
            stored_token = RedisTokenManager.get_refresh_token(user_id)
            if stored_token != refresh_token:
                raise AuthenticationError("Refresh Token이 유효하지 않거나 만료되었습니다.")
            
            user = self.user_service.get_user_by_id(user_id)
            if user is None:
                raise NotFoundError("유저를 찾을 수 없습니다.")
            
            # 새 access token 생성
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub":user.id}, expires_delta=access_token_expires)

            # 새 refresh token 생성
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            new_refresh_token = create_refresh_token(data={"sub":user.id}, expires_delta=refresh_token_expires)

            self.token_manager.store_refresh_token(user.id, new_refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
            self.token_manager.blacklist_token(refresh_token)

            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token
            )
        except (AuthenticationError, NotFoundError) as e:
            raise e
        except Exception as e:
            raise AuthenticationError(f"자격 증명을 검증할 수 없습니다.")
