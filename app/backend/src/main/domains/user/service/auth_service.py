import json
import logging
import secrets

from datetime import timedelta
from asyncio.log import logger
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
import urllib

from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.service.user_service import UserService
from src.main.domains.user.repository.user_repository import UserRepository
from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.domains.user.repository.token_repository import TokenRepository

from src.main.core.config import settings
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError,
    ValidationError
)
from src.main.core.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_service: UserService, token_repository: TokenRepository):
        self.user_service = user_service
        self.token_repository = token_repository

    async def initialize_social_login(self, provider: str) -> str:
        try:
            logger.info(f"소셜 로그인 초기화 중... provider: {provider}")
            social_login = SocialLoginFactory.get_social_login(provider, self.token_repository)
            auth_url = await social_login.get_authorization_url()
            logger.info(f"Authorization URL 생성 완료! auth_url: {auth_url}")
            return auth_url

        except Exception as e:
            logger.exception(f"소셜 로그인 초기화 중 오류 발생: {str(e)}")
            raise InternalServerError(f"소셜 로그인 초기화 중 오류 발생: {str(e)}")
    
    async def handle_oauth_callback(self, request: Request, provider: str) -> JSONResponse:
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        logger.debug(f"전달 받은 state: {state}, provider: {provider}, code: {code}")
        
        if not code or not state:
            raise AuthenticationError("코드 또는 상태 매개 변수가 누락되었습니다.")

        # Redis에서 상태 검증
        if not await self.token_repository.verify_oauth_state(state, provider):
            raise ValidationError("유효하지 않은 상태 매개변수입니다.")
        
        try:
            social_login = SocialLoginFactory.get_social_login(provider, self.token_repository)
            user_create = await social_login.get_user_info(code, state)
            logger.debug(f"생성된 UserCreate 객체: {user_create}")
            
            user = await self.user_service.get_or_create_user(user_create)

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

            user_data = UserResponse.from_orm(user).model_dump()
            encoded_user_data = urllib.parse.quote(json.dumps(user_data))
            
            redirect_url = f"http://localhost:3000/dashboard?user={encoded_user_data}"
            
            response = RedirectResponse(url=redirect_url)

            response.set_cookie(
                key="access_token", 
                value=access_token, 
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 24 * 60 * 60,
                domain="localhost",
                path="/"
            )
            response.set_cookie(
                key="refresh_token", 
                value=refresh_token, 
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                domain="localhost",
                path="/"
            )

            logger.info(f"사용자 정보와 토큰을 포함한 응답을 전송합니다: {response.body}")
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

    async def logout(self, token: str, user_email: str):
        try:
            logger.info(f"Attempting to logout user: {user_email}")
            await self.token_repository.blacklist_token(token)
            await self.token_repository.delete_refresh_token(user_email)
            logger.info(f"이메일이 {user_email} 인 유저가 성공적으로 로그아웃했습니다.")
        except Exception as e:
            logger.error(f"로그아웃 과정 도중 에러 발생: {str(e)}", exc_info=True)
            raise InternalServerError(f"로그아웃 처리 중 예상치 못한 에러 발생: {str(e)}")
