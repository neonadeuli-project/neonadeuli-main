import logging

from asyncio.log import logger
from authlib.integrations.starlette_client import OAuth
from src.main.core.exceptions import InternalServerError
from src.main.core.config import settings

oauth = OAuth()

def setup_oauth():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth 자격 증명이 제대로 구성되지 않았습니다.")
    try:
        # Google Oauth 설정
        oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile',
                'prompt': 'select_account'
            }
        )

        # Naver Oauth 설정
        oauth.register(
            name='naver',
            client_id=settings.NAVER_CLIENT_ID,
            client_secret=settings.NAVER_CLIENT_SECRET,
            authorize_url='https://nid.naver.com/oauth2.0/authorize',
            access_token_url='https://nid.naver.com/oauth2.0/token',
            api_base_url='https://openapi.naver.com/v1/nid/me'
        )

        # Kakao Oauth 설정
        oauth.register(
            name='kakao',
            client_id=settings.KAKAO_REST_API_KEY,
            client_secret=settings.KAKAO_CLIENT_SECRET,
            authorize_url='https://kauth.kakao.com/oauth/authorize',
            access_token_url='https://kauth.kakao.com/oauth/token',
            api_base_url='https://kapi.kakao.com/v2/user/me',
            client_kwargs={'scope': 'profile_nickname profile_image account_email'}
        )

        logging.getLogger('authlib').setLevel(logging.DEBUG)
        
    except Exception as e:
        logger.error(f"OAuth 설정 중 오류 발생: {str(e)}")
        raise InternalServerError(f"OAuth 설정 중 오류 발생: {str(e)}")

    logger.info("Google OAuth 클라이언트가 성공적으로 등록되었습니다.")

    return oauth