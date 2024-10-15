from asyncio.log import logger
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import ValidationError as PydanticValidationError

from src.main.core.exceptions import NotFoundError
from src.main.domains.user.models.user import User
from src.main.core.auth.password import hash_password
from src.main.domains.user.schemas.user import UserResponse
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.repository.user_repository import UserRepository

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"ID가 {user_id}인 사용자를 찾을 수 없습니다")
        
        return user

    async def get_or_create_user(self, user_create: UserCreate) -> UserResponse:
        async with self.db.begin():
            try:
                prepared_data = self._prepare_user_data(user_create)
                user = await self.user_repository.get_by_email(prepared_data['email'])
                if not user:
                    user = await self.user_repository.create_user(prepared_data)
                return UserResponse.from_orm(user)
            except SQLAlchemyError as e:
                logger.error(f"Database error: {str(e)}")
                raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
            except PydanticValidationError as e:
                logger.error(f"Data validation error: {str(e)}")
                raise HTTPException(status_code=422, detail="데이터 검증 오류가 발생했습니다.")
            except Exception as e:
                logger.exception(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"예기치 않은 오류가 발생했습니다: {str(e)}")
    
    def _prepare_user_data(self, user_create: UserCreate) -> dict:
        user_data = user_create.model_dump(exclude_unset=True)
        if user_data.get('password'):
            user_data['password'] = hash_password(user_data['password'])
        if user_data.get('profile_image'):
            user_data['profile_image'] = str(user_data['profile_image'])
        return user_data
    