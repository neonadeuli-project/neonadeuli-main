from asyncio.log import logger
from authlib.integrations.starlette_client import OAuth
from src.main.core.config import settings

oauth = OAuth()

def setup_oauth():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth 자격 증명이 제대로 구성되지 않았습니다.")

    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    logger.info("Google OAuth 클라이언트가 성공적으로 등록되었습니다.")

    # 여기 다른 OAuth 제공자 설정 추가 가능

    return oauth