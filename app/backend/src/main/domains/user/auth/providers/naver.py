import logging

from urllib.parse import urlencode
from fastapi import Request

from src.main.domains.user.schemas.social_auth import NaverUserInfo
from src.main.domains.user.schemas.user.user_create import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase

logger = logging.getLogger(__name__)

class NaverLogin(SocialLoginBase):
    def __init__(self, oauth_client):
        self.oauth_client = oauth_client

    async def get_authorization_url(self, request: Request, state: str) -> str:
        base_url = str(request.base_url)
        redirect_uri = f"{base_url}api/v1/users/auth/naver/callback"
        logger.info(f"Generated redirect_uri: {redirect_uri}")
        params = {
            "response_type": "code",
            "client_id": self.oauth_client.client_id,
            "redirect_uri": redirect_uri,
            "state": state
        }
        return f"{self.oauth_client.authorize_url}?{urlencode(params)}"
    
    async def get_user_info(self, request: Request) -> UserCreate:
        token = await self.oauth_client.authorization_token(request)
        resp = await self.oauth_client.get('', token=token)
        profile=resp.json()
        user_info=profile.get('response', {})

        naver_user=NaverUserInfo(
            email=user_info.get('email'),
            name=user_info.get('name'),
            picture=user_info.get('profile_image')
        )

        return naver_user.to_user_create()