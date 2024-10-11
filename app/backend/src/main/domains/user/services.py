from asyncio.log import logger
from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import ValidationError as PydanticValidationError

from src.main.core.auth.password import hash_password
from src.main.domains.user.schemas.user import UserResponse
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.repositories import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_or_create_user(self, db: AsyncSession, user_create: UserCreate) -> UserResponse:
            try:
                async with db.begin():
                    prepared_data = self._prepare_user_data(user_create)
                    user = await self.user_repository.get_user_by_email(prepared_data['email'])
                    if not user:
                        user = await self.user_repository.create_user(prepared_data)
                    return UserResponse.model_validate(user)
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