import logging
import secrets

from datetime import timedelta
from asyncio.log import logger
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from jose import JWTError

from src.main.domains.user.service.user_service import UserService
from src.main.domains.user.repository.user_repository import UserRepository
from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError
)
from src.main.core.config import settings
from src.main.core.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repository: UserRepository, token_repository: TokenRepository):
        self.user_repository = user_repository
        self.token_repository = token_repository

    async def initialize_social_login(self, request: Request, provider: str) -> str:
        try:
            state = secrets.token_urlsafe(32)
            social_login_class = SocialLoginFactory.get_social_login(provider)
            auth_url = await social_login_class.get_authorization_url(request, state)

            self.token_repository.store_oauth_state(state, provider, 300)

            return {
                "auth_url": auth_url,
                "state": state
            }
        except Exception as e:
            logger.exception(f"소셜 로그인 초기화 중 오류 발생: {str(e)}")
            raise InternalServerError(f"소셜 로그인 초기화 중 오류 발생: {str(e)}")
    
    async def handle_oauth_callback(self, request: Request, provider: str) -> JSONResponse:
        state = request.query_params.get('state')
        if not state:
            raise HTTPException(status_code=400, detail="State parameter is missing")

        # Redis에서 상태 검증
        stored_provider = self.token_repository.get_oauth_state(state)
        if not stored_provider or stored_provider != provider:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        try:
            social_login_class = SocialLoginFactory.get_social_login(provider)
            user_create = await social_login_class.get_user_info(request)
            logger.debug(f"생성된 UserCreate 객체: {user_create}")
            
            user = await self.user_repository.get_or_create_user(user_create)

            access_token = create_access_token(data={"sub": user.email})
            refresh_token = create_refresh_token(data={"sub": str(user.id)})

            logger.info(f"Generated tokens - Access: {access_token[:10]}..., Refresh: {refresh_token[:10]}...")

            # Refresh token 저장
            self.token_repository.store_refresh_token(
                str(user.id),
                refresh_token,
                settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )

            # 사용된 OAuth 상태 삭제
            self.token_repository.delete_oauth_state(state)

            # Set cookies for access and refresh tokens
            response = JSONResponse(content={"message": "로그인 성공", "user": UserResponse.from_orm(user).dict()})
            response.headers["Location"] = "http://localhost:3000/dashboard"
            response.status_code = 302 
            response.set_cookie(
                key="access_token", 
                value=access_token, 
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 24 * 60 * 60
            )
            response.set_cookie(
                key="refresh_token", 
                value=refresh_token, 
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )

            return response

        except AuthenticationError as e:
            logger.exception(f"인증 오류: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"사용자 정보 획득 중 예상치 못한 오류: {str(e)}")
            raise AuthenticationError(f"사용자 정보 획득 중 오류 발생: {str(e)}")


    async def refresh_token(self, request: Request):
        old_refresh_token = request.cookies.get("refresh_token")
        if not old_refresh_token:
            raise AuthenticationError("기존 Refresh Token이 존재하지 않습니다.")
        
        try:
            # refresh token 검증
            payload = verify_token(old_refresh_token)
            user_id = payload.get("sub")

            # 저장된 refresh token과 비교
            stored_token = self.token_repository.get_refresh_token(str(user_id))
            if stored_token != old_refresh_token:
                raise AuthenticationError("Refresh Token이 일치하지 않습니다.")

            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise NotFoundError("유저를 찾을 수 없습니다.")
            
            # 새 access token 생성
            new_access_token = create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )

            # 새 refresh token 생성
            new_refresh_token = create_refresh_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )

            # 새 Refresh 토큰 저장 및 이전 토큰 블랙리스트 처리
            await self.token_repository.store_refresh_token(
                str(user.id), 
                new_refresh_token, 
                settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )
            await self.token_repository.blacklist_token(old_refresh_token)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
        except AuthenticationError as e:
            logger.warning(f"Authentication error in refresh_token: {str(e)}")
            raise
        except NotFoundError as e:
            logger.warning(f"Not found error in refresh_token: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in refresh_token: {str(e)}")
            raise InternalServerError(f"예상치 못한 에러 발생: {str(e)}")

    async def logout(self, user_id: int, token: str):
        await self.token_repository.blacklist_token(token)
        await self.token_repository.delete_refresh_token(str(user_id))
