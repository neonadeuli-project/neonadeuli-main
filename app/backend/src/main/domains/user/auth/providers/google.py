import httpx

from asyncio.log import logger
from urllib.parse import urlencode
from fastapi import Request
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.core.exceptions import AuthenticationError, InternalServerError
from src.main.domains.user.schemas.social_auth import GoogleUserInfo
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase
from src.main.core.config import settings


class GoogleLogin(SocialLoginBase):
    def __init__(self, token_repository: TokenRepository):
        self.token_repository = token_repository
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.authorize_url = settings.GOOGLE_AUTHORIZE_URL
        self.token_url = settings.GOOGLE_TOKEN_URL
        self.userinfo_url = settings.GOOGLE_USERINFO_URL

    async def get_authorization_url(self) -> str:
        try:
            logger.info(f"get_authorization_url 메서드 진입")
            state = await self.token_repository.store_oauth_state('google')
            logger.info(f"저장 된 상태 값: {state}")
            params = {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
            }
            
            auth_url = f"{self.authorize_url}?{urlencode(params)}"
            logger.info(f"redirect_uri: {self.redirect_uri}")
            logger.info(f"구글 Authorization URL 생성 완료! auth_url: {auth_url}")

            return auth_url
        except Exception as e:
            logger.exception(f"구글 Authorization URL 생성 중 오류 발생: {str(e)}")
            raise
    
    async def get_user_info(self, code: str, state: str) -> UserCreate:
        # state 검증
        if not await self.token_repository.verify_oauth_state(state, 'google'):
            raise AuthenticationError("유효하지 않은 OAuth state")
        
        # state 삭제 (재사용 방지)
        await self.token_repository.delete_oauth_state(state)
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(self.token_url, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            })

        if token_response.status_code != 200:
            raise AuthenticationError(f"액세스 토큰을 검색하지 못했습니다: {token_response.text}")

        access_token = token_response.json().get('access_token')
        logger.debug(f"Access token 획득: {access_token}")

        # 사용자 정보 획득
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

        if user_response.status_code != 200:
            raise AuthenticationError(f"Failed to retrieve user info: {user_response.text}")

        user_info = user_response.json()
        logger.debug(f"사용자 정보 획득: {user_info}")

        google_user = GoogleUserInfo(
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info.get('picture')
        )

        return google_user.to_user_create()
    