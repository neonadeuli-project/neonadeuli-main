import logging

from urllib.parse import urlencode
from fastapi import Request
import httpx

from src.main.core.exceptions import AuthenticationError
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.domains.user.schemas.social_auth import NaverUserInfo
from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase
from src.main.core.config import settings

logger = logging.getLogger(__name__)

class NaverLogin(SocialLoginBase):
    def __init__(self, token_repository: TokenRepository):
        self.token_repository = token_repository
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.redirect_uri = settings.NAVER_REDIRECT_URI
        self.authorize_url = settings.NAVER_AUTHORIZE_URL
        self.token_url = settings.NAVER_TOKEN_URL
        self.userinfo_url = settings.NAVER_USERINFO_URL

    async def get_authorization_url(self) -> str:
        try:
            state = await self.token_repository.store_oauth_state('naver')
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "state": state
            }
            auth_url = f"{self.authorize_url}?{urlencode(params)}"
            logger.info(f"redirect_uri: {self.redirect_uri}")
            logger.info(f"네이버 Authorization URL 생성 완료! auth_url: {auth_url}")

            return auth_url
        except Exception as e:
            logger.exception(f"네이버 Authorization URL 생성 중 오류 발생: {str(e)}")
            raise

    async def get_user_info(self, code: str, state: str) -> UserCreate:
        # state 검증
        if not await self.token_repository.verify_oauth_state(state, 'naver'):
            raise AuthenticationError("유효하지 않은 OAuth state")
        
        # state 삭제 (재사용 방지)
        await self.token_repository.delete_oauth_state(state)
        
        # Get access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(self.token_url, params={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "state": state,
                "redirect_uri": self.redirect_uri
            })

        if token_response.status_code != 200:
            raise AuthenticationError(f"Failed to retrieve access token: {token_response.text}")

        access_token = token_response.json()['access_token']
        logger.debug(f"Access token 획득: {access_token}")

        # 유저 정보 조회
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

        if user_response.status_code != 200:
            raise AuthenticationError(f"Failed to retrieve user info: {user_response.text}")

        user_info = user_response.json()['response']
        logger.debug(f"사용자 정보 획득: {user_info}")

        naver_user = NaverUserInfo(
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info.get('picture')
        )

        return naver_user.to_user_create()