import secrets
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.schemas.auth import AuthResponse
from src.main.domains.user.models.user import User
from src.main.core.auth.jwt import create_access_token
from src.main.domains.user.services import UserService
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError, 
    ValidationError
)
from src.main.domains.user.auth.factory import SocialLoginFactory
from src.main.api.deps import get_current_user

from .dependencies import get_user_service

router = APIRouter()

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
        stored_state = request.session.get('oauth_state')
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
async def refresh_token(refresh_token: str):
    # TODO: Token 갱신 로직 구현
    raise NotImplementedError("Token 갱신 기능이 아직 구현되지 않았습니다.")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # TODO: 로그아웃
    raise NotImplementedError("로그아웃 기능이 아직 구현되지 않았습니다.")

