from abc import ABC, abstractmethod

from fastapi import Request

from src.main.core.auth import oauth
from src.main.domains.user.schemas.user import UserCreate

class SocialLoginBase(ABC):
    def __init__(self):
        # oauth.google이 이미 등록된 후 호출될 수 있도록 인스턴스 속성으로 할당합니다.
        self.oauth_client = oauth.google

    @abstractmethod
    async def get_authorization_url(self, request: Request) -> str:
        pass

    @abstractmethod
    async def get_user_info(cls, request: Request) -> UserCreate:
        pass