from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .services import UserService
from .repositories import UserRepository
from src.main.db.deps import get_db

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)