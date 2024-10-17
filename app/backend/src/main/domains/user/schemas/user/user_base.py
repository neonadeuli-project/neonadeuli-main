from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)

    class Config:
        from_attributes = True