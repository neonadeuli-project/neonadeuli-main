from fastapi import Request
from src.main.domains.user.schemas.social_auth import GoogleUserInfo
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase


class GoogleLogin(SocialLoginBase):
    def __init__(self, oauth_client):
        self.oauth_client = oauth_client

    async def get_authorization_url(self, request: Request, state: str) -> str:
        redirect_uri = request.url_for('auth_callback', provider='google')
        print(f"Generated redirect_uri: {redirect_uri}")  # 리디렉션 URI 출력
        return await self.oauth_client.authorize_redirect(request, redirect_uri, state=state)
    
    async def get_user_info(self, request: Request) -> UserCreate:
        token = await self.oauth_client.authorize_access_token(request)
        print(f"Token received: {token}")

        user_info = token.get("userinfo")
        google_user = GoogleUserInfo(
            email=user_info['email'],
            name=user_info['name'],
            profile_image=user_info.get('picture')
        )

        return google_user.to_user_create()