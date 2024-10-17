import httpx

from asyncio.log import logger
from urllib.parse import urlencode
from fastapi import Request
from fastapi.responses import RedirectResponse
from src.main.core.exceptions import AuthenticationError, InternalServerError
from src.main.domains.user.schemas.social_auth import GoogleUserInfo
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.auth.base import SocialLoginBase


class GoogleLogin(SocialLoginBase):
    def __init__(self, oauth_client):
        self.oauth_client = oauth_client
        self.authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    async def get_authorization_url(self, request: Request, state_token: str) -> str:
        try:
            redirect_uri = str(request.url_for('auth_callback', provider='google'))
            logger.debug(f"생성된 redirect_uri: {redirect_uri}")

            params = {
                'client_id': self.oauth_client.client_id,
                'response_type': 'code',
                'scope': 'openid email profile',
                'redirect_uri': redirect_uri,
                'state': state_token,
                'prompt': 'select_account'
            }
            
            authorize_url = f"{self.authorize_url}?{urlencode(params)}"
            logger.debug(f"생성된 authorize_url: {authorize_url}")

            return authorize_url
        except Exception as e:
            logger.error(f"인증 URL 생성 중 오류 발생: {str(e)}")
            raise InternalServerError(f"인증 URL 생성 중 오류 발생: {str(e)}")
    
    async def get_user_info(self, request: Request) -> UserCreate:
        try:
            logger.debug(f"OAuth callback 요청 받음: {request.url}")

            # state 파라미터 추출 및 검증
            # received_state = request.query_params.get('state')
            # stored_state = request.session.get('oauth_state')
            # if received_state != stored_state:
            #     raise AuthenticationError("유효하지 않은 파라미터입니다.")
            
            # access token 획득
            redirect_uri = str(request.url_for('auth_callback', provider='google'))
            code = request.query_params.get('code')
            
            async with httpx.AsyncClient() as client:
                token_response = await client.post(self.token_url, data={
                    'client_id': self.oauth_client.client_id,
                    'client_secret': self.oauth_client.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                })
        
            if token_response.status_code != 200:
                raise AuthenticationError("Failed to retrieve access token")

            # access_token = await self.oauth_client.authorize_access_token(request)
            access_token = token_response.json().get('access_token')
            logger.debug(f"Access token 획득: {access_token}")

            # 사용자 정보 획득
            async with httpx.AsyncClient() as client:
                userinfo_response = await client.get(self.userinfo_url, headers={
                    'Authorization': f'Bearer {access_token}'
                })

            if userinfo_response.status_code != 200:
                raise AuthenticationError(f"Failed to retrieve user info: {userinfo_response.text}")

            user_info = userinfo_response.json()
            logger.debug(f"사용자 정보 획득: {user_info}")

            google_user = GoogleUserInfo(
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture')
            )

            return google_user.to_user_create()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 요청 중 오류 발생: {e.response.status_code} - {e.response.text}")
            raise AuthenticationError(f"Google API 요청 중 오류: {e.response.status_code}")
        except Exception as e:
            logger.exception(f"사용자 정보 획득 중 예기치 않은 오류: {str(e)}")
            raise InternalServerError("내부 서버 오류가 발생했습니다.")