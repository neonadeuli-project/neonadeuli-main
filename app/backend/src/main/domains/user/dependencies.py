from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .service.user_service import UserService
from .repositories import UserRepository
from src.main.db.deps import get_db

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)