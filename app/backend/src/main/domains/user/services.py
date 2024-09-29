from sqlalchemy.orm import Session

from src.main.domains.user.repositories import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user(self, db: Session, user_id: int):
        return self.user_repository.get_user(db, user_id)