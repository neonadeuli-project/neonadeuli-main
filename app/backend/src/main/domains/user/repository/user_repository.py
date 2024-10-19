from asyncio.log import logger
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    
    async def create_user(self, user_create: UserCreate) -> User:
        if isinstance(user_create, dict):
            user_data = user_create
        else:
            user_data = user_create.model_dump(exclude_unset=True)
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()
        return user
    
    async def get_or_create_user(self, user_create: UserCreate) -> User:
        user = await self.get_by_email(user_create.email)
        if not user:
            user = await self.create_user(user_create)
        return user
    