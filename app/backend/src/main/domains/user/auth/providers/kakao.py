from asyncio.log import logger
from urllib.parse import urlencode
from fastapi import Request
import httpx
from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.core.exceptions import AuthenticationError
from src.main.core.config import settings
from src.main.domains.user.schemas.social_auth import KakaoUserInfo
from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase


class KakaoLogin(SocialLoginBase):
    def __init__(self, token_repository: TokenRepository):
        self.token_repository = token_repository
        self.client_id = settings.KAKAO_REST_API_KEY
        self.client_secret = settings.KAKAO_CLIENT_SECRET
        self.redirect_uri = settings.KAKAO_REDIRECT_URI
        self.authorize_url = settings.KAKAO_AUTHORIZE_URL
        self.token_url = settings.KAKAO_TOKEN_URL
        self.userinfo_url = settings.KAKAO_USERINFO_URL

    async def get_authorization_url(self) -> str:
        try:
            state = await self.token_repository.store_oauth_state('kakao')
            params = {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "state": state,
            }
            auth_url = f"{self.authorize_url}?{urlencode(params)}"
            logger.info(f"redirect_uri: {self.redirect_uri}")
            logger.info(f"카카오 Authorization URL 생성 완료! auth_url: {auth_url}")
            return auth_url
        except Exception as e:
            logger.exception(f"카카오 Authorization URL 생성 중 오류 발생: {str(e)}")
            raise
    
    async def get_user_info(self, code: str, state: str) -> UserCreate:
        # state 검증
        if not await self.token_repository.verify_oauth_state(state, 'kakao'):
            raise AuthenticationError("유효하지 않은 OAuth state")
        
        # state 삭제 (재사용 방지)
        await self.token_repository.delete_oauth_state(state)

        async with httpx.AsyncClient() as client:
            token_response = await client.post(self.token_url, data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code
            })

            if token_response.status_code != 200:
                raise AuthenticationError("액세스 토큰을 검색하지 못했습니다.")
            
            access_token = token_response.json()['access_token']

            user_response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if user_response.status_code!= 200:
                raise AuthenticationError("사용자 정보를 가져오지 못했습니다.")
            
            user_data = user_response.json()

        kakao_account = user_data.get('kakao_account', {})
        kakao_user = KakaoUserInfo(
            email=kakao_account.get('email'),
            name=kakao_account.get('profile', {}).get('nickname'),
            picture=kakao_account.get('profile', {}).get('profile_image_url')
        )

        return kakao_user.to_user_create()
