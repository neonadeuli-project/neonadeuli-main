from datetime import datetime
from pydantic import HttpUrl
from .user_base import UserBase

class UserResponse(UserBase):
    id: int
    profile_image: HttpUrl | None = None
    is_active: bool
    last_login: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True