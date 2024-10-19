from src.main.domains.user.repository.token_repository import TokenRepository
from src.main.domains.user.auth.providers.kakao import KakaoLogin
from src.main.domains.user.auth.providers.naver import NaverLogin
# from src.main.core.auth.oauth import oauth
from .providers.google import GoogleLogin

class SocialLoginFactory:
    @staticmethod
    def get_social_login(provider: str, token_repository: TokenRepository):
        if provider == 'google':
            return GoogleLogin(token_repository)
        elif provider == 'naver':
            return NaverLogin(token_repository)
        elif provider == 'kakao':
            return KakaoLogin(token_repository)
        else:
            raise ValueError(f"지원하지 않는 제공자: {provider}")