from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.main.domains.user.schemas.user import UserCreate
from src.main.core.exceptions import NotFoundError, ValidationError
from src.main.domains.user.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"이메일이 {email} 인 유저가 존재하지 않습니다.")
        return user
    
    async def create_user(self, user_create: UserCreate) -> User:
        try:
            user = User(**user_create.model_dump(exclude_unset=True))
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Error creating user: {str(e)}")