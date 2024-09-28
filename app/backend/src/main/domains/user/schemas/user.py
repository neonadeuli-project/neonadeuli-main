from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True