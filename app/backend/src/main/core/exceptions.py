from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class BaseCustomException(Exception):
    def __init__(self, message: str):
        self.message = message

class NotFoundError(BaseCustomException):
    pass

class ValidationError(BaseCustomException):
    pass

class AuthenticationError(BaseCustomException):
    pass

class AuthorizationError(BaseCustomException):
    pass

# 전역 예외 처리기
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    if isinstance(exc, NotFoundError):
        return JSONResponse(status_code=404, content={"message": exc.message})
    elif isinstance(exc, ValidationError):
        return JSONResponse(status_code=400, content={"message": exc.message})
    elif isinstance(exc, AuthenticationError):
        return JSONResponse(status_code=401, content={"message": exc.message})
    elif isinstance(exc, AuthorizationError):
        return JSONResponse(status_code=403, content={"message": exc.message})
    else:
        return JSONResponse(status_code=500, content={"message": "Internal server error"})