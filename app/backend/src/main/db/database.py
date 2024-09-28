from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.main.core.config import settings

engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=True)

Base = declarative_base()

AsyncSessionLocal = sessionmaker (
    autocommit=False,    # False인 경우 자동으로 트랜잭션 커밋 X   
    autoflush=False,     # True인 경우 쿼리 작업 실행 전 보류 중인 DB 변경 사항을 자동으로 Flush 
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)