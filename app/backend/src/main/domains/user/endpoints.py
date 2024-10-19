import logging
from asyncio.log import logger
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from src.main.domains.user.repository.user_repository import UserRepository
from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.service.auth_service import AuthService
from src.main.domains.user.models.user import User
from src.main.core.config import settings
from src.main.core.auth.jwt import verify_token
from src.main.core.auth.dependencies import get_current_user
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError,
    ValidationError
)

from .dependencies import get_auth_service, get_user_repository

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)


@router.get("/login/{provider}")
async def social_login(
    provider: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        auth_url = await auth_service.initialize_social_login(provider)
        logger.info(f"Auth URL을 성공적으로 생성했습니다. provider: {provider}, auth_url {auth_url}")
        return JSONResponse(content={"auth_url": auth_url})
    except ValueError:
        raise ValidationError(f"지원하지 않는 제공자 : {provider}")
    except Exception as e:
        raise InternalServerError(f"로그인 처리 중 오류 발생: {str(e)}")

@router.get("/auth/{provider}/callback", name="auth_callback")
async def auth_callback(
    request: Request,
    provider: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        logger.debug(f"OAuth 콜백 받음. Provider: {provider}")
        logger.debug(f"요청 쿼리 파라미터: {request.query_params}")
        
        auth_response = await auth_service.handle_oauth_callback(request, provider)
        logger.debug(f"인증 응답 생성됨")
        return auth_response
    except ValidationError as e:
        logger.error(f"State 검증 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        logger.error(f"인증 오류: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.exception(f"예상치 못한 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")

@router.post("/token/refresh")
async def refresh_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise AuthenticationError("Refresh token을 찾을 수 없습니다.")
    
    try:
        new_tokens = await auth_service.refresh_token(request)
        response = JSONResponse(content={"access_token": new_tokens["access_token"]})
        response.set_cookie(
            key="refresh_token",
            value=new_tokens["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        return response
    except AuthenticationError as e:
        if str(e) == "Refresh Token이 존재하지 않습니다.":
            raise HTTPException(status_code=401, detail="No refresh token found")
        raise HTTPException(status_code=401, detail=str(e))
    except NotFoundError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        raise InternalServerError(f"예상치 못한 에러 발생: {str(e)}")

@router.get("/info", response_model=UserResponse)
async def read_user_info(
    request: Request, 
    user_repository: UserRepository = Depends(get_user_repository)
):
    user = request.state.user
    logger.info(f"UserInfo 조회 시도. User: {user.id if user else 'None'}")

    if not user:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="No access token provided")
        
        try:
            payload = verify_token(token)
            email = payload.get("sub")
            user = await user_repository.get_by_email(email)
            
            logger.info(f"Verifying token: {token[:10]}...")
            logger.info(f"Payload: {payload}")
            logger.info(f"User found: {user}")
        except Exception as e:
            logger.error(f"토큰 검증 실패: {str(e)}")
            raise AuthenticationError("유효하지 않은 토큰입니다.", {str(e)})

    if not user:
        raise NotFoundError("유저를 찾을 수 없습니다.")
    
    logger.info(f"유저 정보 반환: ID {user.id}")
    return UserResponse.from_orm(user)

@router.post("/logout")
async def logout(
    current_user_and_token: Tuple[User, str] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    current_user, token = current_user_and_token
    try:    
        await auth_service.logout(token, current_user.email)

        response = JSONResponse(content={"message": "로그아웃 성공"})
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return response
    except Exception as e:
        logger.error(f"로그아웃 에러 발생: {str(e)}", exc_info=True)
        raise InternalServerError("로그아웃 처리 중 오류가 발생했습니다.")

