from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.backend.src.main.db.database import Base
    
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    # oauth_id = Column(String(255), unique=True, index=True, nullable=True)
    # email = Column(String(255), unique=True, index=True)
    name = Column(String(100))
    # provider = Column(String(255), nullable=True)
    # hashed_password = Column(String(255), nullable=True)
    # is_active = Column(Boolean, default=True)
    # role = Column(Enum(UserRole), default=UserRole.USER)
    token = Column(String(255), unique=True, index=True)
    # refresh_token = Column(String(255), unique=True, index=True, nullable=True)
    # refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())