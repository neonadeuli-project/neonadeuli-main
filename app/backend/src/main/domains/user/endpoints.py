import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from src.main.domains.user.service.auth_service import AuthService
from src.main.domains.user.schemas.auth import RefreshTokenResponse
from src.main.domains.user.models.user import User
from src.main.core.auth.dependencies import get_current_user, oauth2_scheme
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError, 
    ValidationError
)

from .dependencies import get_auth_service

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

@router.get("/login/{provider}")
async def social_login(
    request: Request,
    provider: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        auth_url = await auth_service.initialize_social_login(request, provider)
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
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        auth_response = await auth_service.handle_oauth_callback(request, provider, state)
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
    auth_service: AuthService = Depends(get_auth_service)
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
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.logout(current_user.id, token)
        return {"message": "로그아웃 성공"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다."
        )

