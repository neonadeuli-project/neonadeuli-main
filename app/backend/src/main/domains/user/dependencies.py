from fastapi import Depends
from sqlalchemy.orm import Session
from .services import UserService
from .repositories import UserRepository
from ...db.deps import get_db

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)