from pydantic import Field, HttpUrl
from .user_base import UserBase

class UserCreate(UserBase):
    profile_image: str | None = None
    is_active: bool = Field(default=True)
    password: str | None = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, oauth_info: dict):
        return cls(
            email=oauth_info['email'],
            name=oauth_info['name'],
            profile_image=oauth_info.get("picture")
        )