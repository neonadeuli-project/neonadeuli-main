from fastapi import APIRouter, Depends, HTTPException, Request

from src.main.domains.user.models.user import User
from src.main.core.auth.jwt import create_access_token
from src.main.domains.user.services import UserService
from src.main.core.exceptions import (
    AuthenticationError, 
    NotFoundError, 
    ValidationError
)
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.api.deps import get_current_user

from .dependencies import get_user_service

router = APIRouter()

@router.get("/login/{provider}")
async def social_login(
    request: Request,
    provider: str
):
    try:
        social_login_class = SocialLoginFactory.get_social_login(provider)
        return await social_login_class.get_authorization_url(request)
    except ValueError:
        raise NotFoundError(f"지원하지 않는 제공자 : {provider}")

@router.get("/auth/{provider}/callback")
async def auth_callback(
    request: Request,
    provider: str,
    user_service: UserService = Depends(get_user_service)
):
    try:
        social_login_class = SocialLoginFactory.get_social_login(provider)
        user_create = await social_login_class.get_user_info(request)

        user = await user_service.get_or_create_user(user_create)
        access_token = create_access_token(data={"sub": user.email})

        return {"access_token": access_token, "token_type": "bearer"}
    
    except ValueError:
        raise NotFoundError(f"지원하지 않는 제공자: {provider}")
    except (AuthenticationError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/token/refresh")
async def refresh_token(refresh_token: str):
    # TODO: Token 갱신 로직 구현
    raise NotImplementedError("Token 갱신 기능이 아직 구현되지 않았습니다.")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # TODO: 로그아웃
    raise NotImplementedError("로그아웃 기능이 아직 구현되지 않았습니다.")

