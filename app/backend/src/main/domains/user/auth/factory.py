from src.main.domains.user.auth.providers.naver import NaverLogin
from src.main.core.auth.oauth import oauth
from .providers.google import GoogleLogin

class SocialLoginFactory:
    @staticmethod
    def get_social_login(provider: str):
        if provider == 'google':
            return GoogleLogin(oauth.google)
        elif provider == 'naver':
            return NaverLogin(oauth.naver)
        # elif provider == 'kakao':
        #     return KakaoLogin
        else:
            raise ValueError(f"지원하지 않는 제공자: {provider}")