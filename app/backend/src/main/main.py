import sys
import os
import logging

import redis

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from fastapi.routing import APIRoute
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.main.middleware.auth import auth_middleware
from src.main.core.auth.oauth import setup_oauth
from src.main.db.database import Base, engine
from src.main.core.config import settings
from src.main.api.v1.api import api_router
from src.main.db.database import redis_client
from src.main.core.exceptions import BaseCustomException, custom_exception_handler

logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.info("애플리케이션 시작 프로세스 시작")
    setup_oauth()
    # Redis 연결 확인
    try:
        redis_client.ping()
        logger.info("Redis 서버 연결 성공")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis 서버 연결 실패: {e}")

    async with engine.begin() as conn:
        # 모든 테이블 삭제
        # logger.info("테이블 삭제 중")
        # await conn.run_sync(Base.metadata.drop_all)
        # 모든 테이블 다시 생성
        logger.info("테이블 생성 중")
        await conn.run_sync(Base.metadata.create_all)

        # 생성된 테이블 목록 로깅
        tables = Base.metadata.tables
        logger.info(f"생성된 테이블: {', '.join(tables.keys())}")
        
    logger.info("애플리케이션 시작 프로세스 완료")
    yield
    # 애플리케이션 종료 시 실행될 로직 (필요한 경우)


def create_application() -> FastAPI:
    app = FastAPI(
        lifespan=app_lifespan,
        # 배포 시 swagger UI, Redoc 비활성화
        # docs_url= None,
        # redoc_url= None,
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
    )

    app.add_exception_handler(BaseCustomException, custom_exception_handler)
    app.add_middleware(SessionMiddleware, secret_key=settings.BACKEND_SESSION_SECRET_KEY)
    app.middleware("http")(auth_middleware)

    # Set All CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)