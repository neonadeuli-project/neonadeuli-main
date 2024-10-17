from pydantic import AnyHttpUrl, BaseModel, EmailStr
from .user import UserCreate

class BaseUserInfo(BaseModel):
    email: EmailStr
    name: str
    picture: AnyHttpUrl | None = None

    def to_user_create(self) -> UserCreate:
        return UserCreate(
            email=self.email,
            name=self.name,
            profile_image=str(self.picture) if self.picture else None,
            password=None
        )
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, oauth_info: dict):
        return cls(
            email=oauth_info['email'],
            name=oauth_info['name'],
            profile_image=str(oauth_info.get("picture")) if oauth_info.get("picture") else None
        )

class GoogleUserInfo(BaseUserInfo): 
    pass

class NaverUserInfo(BaseUserInfo):
    pass

class KakaoUserInfo(BaseUserInfo):
    pass

# 필요한 경우 각 제공자별로 추가적인 필드나 메서드를 정의
# 예를 들어:
# class KakaoUserInfo(BaseUserInfo):
#     age_range: str | None = None
#     gender: str | None = None
