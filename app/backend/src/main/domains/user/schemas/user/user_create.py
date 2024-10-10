from pydantic import HttpUrl
from .user_base import UserBase

class UserCreate(UserBase):
    password: str
    profile_image: HttpUrl | None = None

    class Config:
        from_attributes = True