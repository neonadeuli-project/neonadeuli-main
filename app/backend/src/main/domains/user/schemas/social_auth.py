from pydantic import BaseModel, EmailStr, HttpUrl
from .user import UserCreate

class BaseUserInfo(BaseModel):
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

class GoogleUserInfo(BaseUserInfo): 
    pass

class NaverUserInfo(BaseUserInfo):
    pass

# 필요한 경우 각 제공자별로 추가적인 필드나 메서드를 정의
# 예를 들어:
# class KakaoUserInfo(BaseUserInfo):
#     age_range: str | None = None
#     gender: str | None = None
