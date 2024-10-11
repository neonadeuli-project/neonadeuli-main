from abc import ABC, abstractmethod

from fastapi import Request

from src.main.core.auth import oauth
from src.main.domains.user.schemas.user import UserCreate

class SocialLoginBase(ABC):
    @abstractmethod
    async def get_authorization_url(self, request: Request) -> str:
        pass

    @abstractmethod
    async def get_user_info(cls, request: Request) -> UserCreate:
        pass