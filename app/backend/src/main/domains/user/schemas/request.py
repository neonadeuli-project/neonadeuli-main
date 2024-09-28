from pydantic import BaseModel, EmailStr

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    password: str | None = None