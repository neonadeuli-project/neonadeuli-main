"""
인증 관련 기능을 제공하는 패키지입니다.

JWT 토큰 처리, OAuth 인증, 그리고 사용자 인증을 위한 의존성 함수를 포함합니다.
"""

from .jwt import create_access_token, verify_token
from .oauth import setup_oauth
from .dependencies import get_current_user

__all__ = ['create_access_token', 'verify_token', 'setup_oauth', 'get_current_user']