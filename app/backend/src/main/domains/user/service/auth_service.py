import secrets
import logging

from datetime import timedelta
from fastapi import Request

from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.domains.user.repository.user_repository import UserRepository
from src.main.domains.user.schemas.auth import AuthResponse, RefreshTokenResponse
from src.main.core.exceptions import (
    AuthenticationError, 
    NotFoundError, 
    ValidationError
)
from src.main.core.config import settings
from src.main.core.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)

logging.basicConfig(level=logging.DEBUG)

class AuthService:
    def __init__(self, user_repository: UserRepository, token_repository: TokenRepository):
        self.user_repository = user_repository
        self.token_repository = token_repository

    async def initialize_social_login(self, request: Request, provider: str) -> str:
        social_login_class = SocialLoginFactory.get_social_login(provider)
        state = secrets.token_urlsafe()
        request.session['oauth_state'] = state
        logging.debug(f"생성된 state 값: {state}") 
        logging.debug(f"state 저장 이후 세션 값: {request.session}")
        return await social_login_class.get_authorization_url(request, state)
    
    async def handle_oauth_callback(self, request: Request, provider: str, state: str) -> AuthResponse:
        logging.debug(f"전달받은 state 값: {state}")
        stored_state = request.session.get('oauth_state')
        logging.debug(f"세션에 저장된 state 값: {stored_state}")
        if state != stored_state:
            raise ValidationError("유효하지 않은 State 파라미터입니다.")
            
        social_login_class = SocialLoginFactory.get_social_login(provider)
        user_create = await social_login_class.get_user_info(request)
        
        user = await self.user_repository.get_or_create_user(user_create)
        access_token = create_access_token(data={"sub": user.email})

        return AuthResponse.create(UserResponse.from_orm(user), access_token)

    async def refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("유효하지 않은 Refresh Token입니다.")
            
            stored_token = TokenRepository.get_refresh_token(user_id)
            if stored_token != refresh_token:
                raise AuthenticationError("Refresh Token이 유효하지 않거나 만료되었습니다.")
            
            user = self.user_repository.get_by_id(user_id)
            if user is None:
                raise NotFoundError("유저를 찾을 수 없습니다.")
            
            # 새 access token 생성
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub":user.id}, expires_delta=access_token_expires)

            # 새 refresh token 생성
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            new_refresh_token = create_refresh_token(data={"sub":user.id}, expires_delta=refresh_token_expires)

            self.token_repository.store_refresh_token(user.id, new_refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
            self.token_repository.blacklist_token(refresh_token)

            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token
            )
        except (AuthenticationError, NotFoundError) as e:
            raise e
        except Exception as e:
            raise AuthenticationError(f"자격 증명을 검증할 수 없습니다.")
    
    async def logout(self, user_id: int, token: str):
        await self.token_repository.blacklist_token(token)
        await self.token_repository.delete_refresh_token(str(user_id))
