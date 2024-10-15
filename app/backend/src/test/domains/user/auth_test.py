import sys
import os
from dotenv import load_dotenv
from unittest.mock import patch
from starlette.middleware.sessions import SessionMiddleware
from fastapi.testclient import TestClient
from src.main.core.auth.oauth import setup_oauth
from src.main.main import app

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

# 테스트 전 OAuth 설정 호출
setup_oauth()
app.add_middleware(SessionMiddleware, secret_key="test_secret_key")

client = TestClient(app)

@patch('src.main.core.auth.oauth.oauth')
def test_login_endpoint(mock_oauth):
    # Google OAuth 모킹 설정
    mock_google = mock_oauth.register.return_value
    mock_google.authorize_access_token.return_value = {
        "access_token": "mock_access_token"
    }
    mock_google.parse_id_token.return_value = {
        "sub": "1234567890",
        "email": "test@example.com",
        "name": "Test User"
    }

    # 실제 테스트 실행
    response = client.get("/api/v1/users/login/google")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 200