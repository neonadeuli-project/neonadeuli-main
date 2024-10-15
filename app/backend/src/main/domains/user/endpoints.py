import secrets
import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from src.main.domains.user.service import auth_service
from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.schemas.auth import AuthResponse, RefreshTokenResponse
from src.main.domains.user.models.user import User
from src.main.core.auth.dependencies import oauth2_scheme
from src.main.core.config import settings
from src.main.core.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)

from src.main.domains.user.service.user_service import UserService
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError, 
    ValidationError
)
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.api.deps import get_current_user

from .dependencies import get_auth_service, get_user_service

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

@router.get("/login/{provider}")
async def social_login(request: Request,provider: str):
    try:
        social_login_class = SocialLoginFactory.get_social_login(provider)
        state = secrets.token_urlsafe()
        request.session['oauth_state'] = state
        print(f"Generated state: {state}") 
        auth_url = await social_login_class.get_authorization_url(request, state)
        return JSONResponse(content={"auth_url": auth_url})
    except ValueError:
        raise NotFoundError(f"지원하지 않는 제공자 : {provider}")
    except Exception as e:
        raise InternalServerError(f"로그인 처리 중 오류 발생: {str(e)}")

@router.get("/auth/{provider}/callback", name="auth_callback")
async def auth_callback(
    request: Request,
    provider: str,
    state: str = Query(...),
    user_service: UserService = Depends(get_user_service)
):
    try:
        logging.debug(f"전달받은 state 값: {state}")
        stored_state = request.session.get('oauth_state')
        logging.debug(f"세션에 저장된 state 값: {stored_state}")
        if state != stored_state:
            raise ValidationError("유효하지 않은 State 파라미터입니다.")
            
        social_login_class = SocialLoginFactory.get_social_login(provider)
        user_create = await social_login_class.get_user_info(request)

        user = await user_service.get_or_create_user(user_create)
        access_token = create_access_token(data={"sub": user.email})

        auth_response = AuthResponse.create(UserResponse.from_orm(user), access_token)

        return auth_response.to_response()
    
    except ValueError:
        raise NotFoundError(f"지원하지 않는 제공자: {provider}")
    except AuthenticationError as e:
        raise AuthenticationError(str(e))
    except Exception as e:
        raise InternalServerError(f"인증 콜백 처리 중 오류 발생: {str(e)}")

@router.get("/token/refresh")
async def refresh_token(
    refresh_token: str = Depends(oauth2_scheme), 
    auth_service: auth_service.AuthService = Depends(get_auth_service)
):
    try:
        tokens = await auth_service.refresh_token(refresh_token)
        return RefreshTokenResponse(**tokens)
    except AuthenticationError as e:
        raise AuthenticationError(str(e))
    except NotFoundError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        raise InternalServerError(f"예상치 못한 에러 발생: {str(e)}")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # TODO: 로그아웃
    raise NotImplementedError("로그아웃 기능이 아직 구현되지 않았습니다.")

