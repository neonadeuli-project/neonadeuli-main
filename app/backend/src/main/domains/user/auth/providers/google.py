from fastapi import Request
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase


class GoogleLogin(SocialLoginBase):
    def __init__(self, oauth_client):
        self.oauth_client = oauth_client

    @classmethod
    async def get_authorization_url(cls, request: Request) -> str:
        redirect_uri = request.url_for('auth_callback', provider='google')
        return await cls.oauth_client.authorize_redirect(request, redirect_uri)
    
    @classmethod
    async def get_user_info(cls, request: Request) -> UserCreate:
        token = await cls.oauth_client.authorize_access_token(request)
        user_info = await cls.oauth_client.authorize_access_token(request)
        return UserCreate(
            email=user_info['email'],
            name=user_info['name'],
            profile_image=user_info.get('picture')
        )