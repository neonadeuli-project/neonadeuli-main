from fastapi import APIRouter
from app.backend.src.main.domains.user import endpoints as user_endpoints
from app.backend.src.main.domains.chat import endpoints as chat_endpoints
# 다른 도메인의 엔드포인트들도 여기에 임포트합니다.

api_router = APIRouter()

api_router.include_router(user_endpoints.router, prefix="/users", tags=["users"])
# 다른 도메인의 라우터들도 여기에 포함시킵니다.

@api_router.get("/health-check")
def health_check():
    return {"status": "ok"}