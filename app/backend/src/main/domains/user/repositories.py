from asyncio.log import logger
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main.core.auth.password import hash_password
from src.main.domains.user.schemas.user import UserCreate
from src.main.domains.user.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    
    async def create_user(self, user_create: UserCreate) -> User:
        user = User(**user_create.model_dump(exclude_unset=True))
        self.db.add(user)
        await self.db.flush()
        return user