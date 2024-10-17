from pydantic import HttpUrl

from .user_base import UserBase

class UserUpdate(UserBase):
    name: str | None = None
    email: str | None = None
    profile_image: HttpUrl | None = None

    class Config:
        from_attributes = True