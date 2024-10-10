from sqlalchemy import Enum


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"