from pydantic import BaseModel, EmailStr, HttpUrl
from .user import UserCreate

class GoogleUserInfo(BaseModel):
    email: EmailStr
    name: str
    picture: HttpUrl | None = None

    def to_user_create(self) -> UserCreate:
        return UserCreate(
            email=self.email,
            name=self.name,
            profile_image=self.picture,
            password=None
        )
    
    class Config:
        from_attributes = True