from pydantic import BaseModel

from .user import UserResponse


class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class AuthResponse(BaseModel):
    content: LoginResponse
    access_token: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, user: UserResponse, access_token: str) -> 'AuthResponse':
        return cls(
            content=LoginResponse(
                message="로그인 성공",
                user=user
            ),
            access_token=access_token
        )

    def to_response(self):
        from fastapi.responses import JSONResponse

        response = JSONResponse(content=self.content.model_dump())
        response.set_cookie(
            key="access_token",
            value=f"Bearer {self.access_token}",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600
        )

        return response