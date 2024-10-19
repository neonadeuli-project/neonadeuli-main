from asyncio.log import logger
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.main.core.auth.jwt import verify_token
from src.main.domains.user.dependencies import get_redis_token_manager, get_user_repository
from src.main.db.deps import get_db

security = HTTPBearer()

async def auth_middleware(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    logger.info(f"Cookies: {request.cookies}")
    logger.info(f"Headers: {request.headers}")

    # 정적 리소스 요청 무시
    if request.url.path in ['/favicon.ico', '/static']:
        return await call_next(request)
    
    # 토큰 갱신 엔드포인트 미들웨어 통과
    if request.url.path == "/api/v1/users/token/refresh":
        return await call_next(request)
    
    # 로그인, 콜백 엔드포인트 미들웨어 통과
    if request.url.path.startswith("/api/v1/users/login") or request.url.path.startswith("/api/v1/users/auth"):
        return await call_next(request)
    
    try:
        # DB 세션 획득
        db = await get_db().__anext__()
        token_manager = get_redis_token_manager()
        user_repository = get_user_repository(db)

        # 토큰 추출
        token = request.cookies.get("access_token")
        if not token:
            auth: HTTPAuthorizationCredentials = await security(request)
            if auth:
                token = auth.credentials
        
        if token:
            try:
                # 토큰 검증
                payload = verify_token(token)
                logger.info(f"토큰 인증 성공: {payload}")
                
                user_email = payload.get("sub")
                user = await user_repository.get_by_email(user_email)
                if user:
                    request.state.user = user
                    logger.info(f"User authenticated: {user_email}")
                else:
                    logger.warning(f"User not found for email: {user_email}")
                    request.state.user = None

                logger.info(f"인증된 유저: {user_email}")
            except Exception as e:
                logger.error(f"토큰 인증 실패: {str(e)}")
                request.state.user = None
        else:
            logger.info("access token을 찾을 수 없습니다.")
            request.state.user = None
    except Exception as e:
        logger.error(f"인증 미들웨어 에러: {str(e)}")
        request.state.user = None
    finally:
        if db:
            await db.close()

    response = await call_next(request)
    return response