from datetime import datetime
from typing import Optional
from pydantic import HttpUrl, validator
from .user_base import UserBase

class UserResponse(UserBase):
    id: int
    profile_image: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

    @validator('last_login', 'created_at', pre=True)
    def parse_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, str):
            return value
        elif value is None:
            return None
        raise ValueError(f'Invalid datetime format: {value}')

    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_image=str(user.profile_image) if user.profile_image else None,
            is_active=user.is_active,
            last_login=cls.parse_datetime(user.last_login),
            created_at=cls.parse_datetime(user.created_at)
        )