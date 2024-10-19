import os
from pathlib import Path
from typing import Annotated, Any
from dotenv import load_dotenv

from pydantic import (
    AnyUrl,
    BeforeValidator
)

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)

current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent.parent
env_path = backend_dir / '.env'
load_dotenv()

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True, 
        extra="ignore",
        env_file_encoding="utf-8"
    )

    # Info
    PROJECT_NAME : str
    API_V1_STR: str
    LOG_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    
    # Server
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ]
    BACKEND_SESSION_SECRET_KEY : str

    # DB
    SQLALCHEMY_DATABASE_URI: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PWD: str

    # Oauth2.0
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_AUTHORIZE_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_USERINFO_URL: str

    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    NAVER_REDIRECT_URI: str
    NAVER_AUTHORIZE_URL: str
    NAVER_TOKEN_URL: str
    NAVER_USERINFO_URL: str

    KAKAO_REST_API_KEY: str
    KAKAO_CLIENT_SECRET: str
    KAKAO_REDIRECT_URI: str
    KAKAO_AUTHORIZE_URL: str
    KAKAO_TOKEN_URL: str
    KAKAO_USERINFO_URL: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    OAUTH_STATE_EXPIRE_SECONDS: int
    
    # Token
    SECRET_KEY: str
    ALGORITHM: str

settings = Settings()