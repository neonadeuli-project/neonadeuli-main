from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.main.domains.user.schemas.user import UserResponse
from src.main.core.exceptions import ValidationError
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.repositories import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_or_create_user(self, user_create: UserCreate) -> UserResponse:
        try:
            user = await self.user_repository.get_user_by_email(user_create.email)
            if not user:
                user = await self.user_repository.create_user(user_create)
            return UserResponse.model_validate(user)
        except Exception as e:
            raise ValidationError("유저 생성 또는 조회 오류 : {str(e)}")
    