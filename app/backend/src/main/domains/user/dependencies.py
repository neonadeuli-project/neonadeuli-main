from fastapi import Depends
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.main.domains.user.repository.token_repository import TokenRepository
from .service.user_service import UserService
from .repository.user_repository import UserRepository
from src.main.db.deps import get_db
from src.main.db.database import redis_client

def get_redis_client() -> Redis:
    return redis_client

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

def get_redis_token_manager() -> TokenRepository:
    return TokenRepository(redis_client)

def get_auth_service(
        user_service: UserService = Depends(get_user_service),
        token_manager: TokenRepository = Depends(get_redis_token_manager)
):
    from src.main.domains.user.service.auth_service import AuthService
    return AuthService(user_service, token_manager)