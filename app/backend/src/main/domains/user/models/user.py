from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.main.core.enum import UserRole
from src.main.db.database import Base
    
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    profile_image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # oauth_id = Column(String(255), unique=True, index=True, nullable=True)
    # oauth_provider = Column(String(50), nullable=True)

    # is_active = Column(Boolean, default=True)
    # role = Column(Enum(UserRole), default=UserRole.USER)

    # access_token = Column(String(255), unique=True, index=True, nullable=True)
    # access_expires_at = Column(DateTime(timezone=True), nullable=True)

    # refresh_token = Column(String(255), unique=True, index=True, nullable=True)
    # refresh_expires_at = Column(DateTime(timezone=True), nullable=True)

