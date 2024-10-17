import logging
from asyncio.log import logger

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from src.main.core.auth.jwt import verify_token
from src.main.domains.user.service.user_service import UserService
from src.main.domains.user.schemas.user.user_response import UserResponse
from src.main.domains.user.service.auth_service import AuthService
from src.main.core.config import settings
from src.main.domains.user.models.user import User
from src.main.core.auth.dependencies import get_current_user, oauth2_scheme
from src.main.core.exceptions import (
    AuthenticationError,
    InternalServerError, 
    NotFoundError,
    ValidationError
)

from .dependencies import get_auth_service, get_user_service

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

@router.get("/login/{provider}")
async def social_login(
    request: Request,
    provider: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        response_data = await auth_service.initialize_social_login(request, provider)
        logger.debug(f"생성된 response_data: {response_data['auth_url']}")

        return JSONResponse(content=response_data)
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
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        new_tokens = await auth_service.refresh_token(request)
        response.set_cookie(
            key="refresh_token",
            value=new_tokens["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        return {
            "access_token": new_tokens["access_token"],
            "token_type": "bearer"
        }
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
    user_service: UserService = Depends(get_user_service)
):
    user = request.state.user
    logger.info(f"UserInfo 조회를 시도했습니다. request state 안 User: {user}")
    if not user:
        logger.warning("request state 에서 유저를 찾을 수 없습니다.")
        authorization: str = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
                user = await user_service.get_user_by_id(user_id)
                if user:
                    logger.info(f"ID가 {user_id}인 유저를 찾았습니다.")
                else:
                    logger.warning(f"ID가 {user_id}인 유저를 찾을 수 없습니다.")
            except Exception as e:
                logger.error(f"토큰 인증 실패: {str(e)}")
    if not user:
        raise AuthenticationError("인증되지 않은 사용자입니다.")
    
    logger.info(f"사용자 ID가 {user.id}인 유저 정보를 반환합니다.")
    return UserResponse.from_orm(user)

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

