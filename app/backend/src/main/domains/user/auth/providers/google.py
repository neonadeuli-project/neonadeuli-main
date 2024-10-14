from urllib.parse import urlencode
from fastapi import Request
from src.main.core.exceptions import AuthenticationError, InternalServerError
from src.main.domains.user.schemas.social_auth import GoogleUserInfo
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase


class GoogleLogin(SocialLoginBase):
    def __init__(self, oauth_client):
        self.oauth_client = oauth_client

    async def get_authorization_url(self, request: Request, state: str) -> str:
        try:
            redirect_uri = str(request.url_for('auth_callback', provider='google'))
            print(f"Generated redirect_uri: {redirect_uri}")  # 리디렉션 URI 출력
            params = {
                "response_type": "code",
                "client_id": self.oauth_client.client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid email profile",
                "state": state
            }
            
            auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
            auth_url = f"{auth_endpoint}?{urlencode(params)}"
            
            return auth_url
        except Exception as e:
            raise InternalServerError(f"인증 URL 생성 중 오류 발생: {str(e)}")
    
    async def get_user_info(self, request: Request) -> UserCreate:
        try:
            token = await self.oauth_client.authorize_access_token(request)

            print(f"Token received: {token}")
            user_info = await self.oauth_client.parse_id_token(request, token)

            google_user = GoogleUserInfo(
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture')
            )

            return google_user.to_user_create()
        except Exception as e:
            raise AuthenticationError(f"사용자 정보 획득 중 오류 발생: {str(e)}")