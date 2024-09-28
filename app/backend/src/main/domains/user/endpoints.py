from fastapi import APIRouter, Depends
from .services import UserService
from .dependencies import get_user_service

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_user(user_id)