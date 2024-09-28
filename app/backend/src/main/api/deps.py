from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.backend.src.main.core.config import settings
from app.backend.src.main.db.deps import get_db
from app.backend.src.main.domains.user.services import UserService
from app.backend.src.main.domains.user.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        details="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate":"Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithm=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = user_service.get_user_by_name(username)
    if user is None:
        raise credentials_exception
    return user


