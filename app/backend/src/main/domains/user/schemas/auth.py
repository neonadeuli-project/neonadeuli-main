from pydantic import BaseModel

from .user import UserResponse


class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class AuthResponse(BaseModel):
    content: LoginResponse
    tokens: TokenResponse

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, user: UserResponse, access_token: str, refresh_token: str) -> 'AuthResponse':
        return cls(
            content=LoginResponse(
                message="로그인 성공",
                user=user
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
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