from typing import Any, Dict
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from .user import UserResponse
from src.main.core.config import settings


class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class AuthResponse(BaseModel):
    user: UserResponse
    message: str = "로그인 성공"

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, user: UserResponse):
        return cls(
            user=user,
            message="로그인 성공"
        )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return {
            "message": self.message,
            "user": self.user.model_dump()
        }
    
class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    @classmethod
    def create(cls, access_token: str, refresh_token: str) -> 'RefreshTokenResponse':
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )