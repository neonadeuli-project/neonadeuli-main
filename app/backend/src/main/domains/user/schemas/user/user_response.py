from datetime import datetime
from pydantic import HttpUrl
from .user_base import UserBase

class UserResponse(UserBase):
    id: int
    profile_image: HttpUrl | None = None
    is_active: bool
    last_login: str | None
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, db_user):
        return cls(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            profile_image=db_user.profile_image,
            is_active=db_user.is_active,
            last_login=db_user.last_login.isoformat() if isinstance(db_user.last_login, datetime) else db_user.last_login,
            created_at=db_user.created_at.isoformat() if isinstance(db_user.created_at, datetime) else db_user.created_at
        )