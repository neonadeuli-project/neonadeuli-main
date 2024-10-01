from sqlalchemy.orm import Session
from . import models, schemas

class UserRepository:
    def get_user(self, db: Session, user_id: int):
        return db.query(models.User).filter(models.User.id == user_id).first()

    # def create_user(self, db: Session, user: schemas.UserCreate):
    #     db_user = models.User(email=user.email, hashed_password=user.password)  # 실제로는 비밀번호를 해시화해야 합니다
    #     db.add(db_user)
    #     db.commit()
    #     db.refresh(db_user)
    #     return db_user