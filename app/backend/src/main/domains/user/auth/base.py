from abc import ABC, abstractmethod
from fastapi import Request
from src.main.domains.user.schemas.user import UserCreate

class SocialLoginBase(ABC):
    @abstractmethod
    async def get_authorization_url(self, request: Request, state_token: str) -> str:
        """
        OAuth 인증 URL을 생성합니다.
        
        :param request: FastAPI Request 객체
        :param state_token: JWT 형식의 state 토큰
        :return: 인증 URL 문자열
        """
        pass

    @abstractmethod
    async def get_user_info(self, request: Request) -> UserCreate:
        """
        OAuth 제공자로부터 사용자 정보를 가져옵니다.
        
        :param request: FastAPI Request 객체
        :return: UserCreate 객체
        """
        pass