// Updated front-end and back-end code to use cookies instead of local storage for storing tokens.

// FRONT-END (React Code Update)
import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation, useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/auth/:provider/callback" element={<OAuthCallback />} />
        <Route path="/" element={<Home />} />
      </Routes>
    </Router>
  );
};

const Home = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const fetchUserInfo = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/info`, {
        credentials: 'include', // Include cookies in the request
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsLoggedIn(true);
      } else {
        throw new Error('사용자 정보를 가져오는데 실패했습니다.');
      }
    } catch (error) {
      setError(error.message);
    }
  }, []);

  useEffect(() => {
    fetchUserInfo();
  }, [fetchUserInfo]);

  const handleSocialLogin = async (provider) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/login/${provider}`);
      const data = await response.json();
      if (data.auth_url && data.state) {
        window.location.href = data.auth_url;
      } else {
        throw new Error('인증 URL 또는 상태 토큰이 제공되지 않았습니다.');
      }
    } catch (error) {
      console.error('로그인 초기화 중 오류 발생:', error);
      setError(error.message || '로그인 프로세스 중 오류가 발생했습니다.');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/logout`, {
        method: 'POST',
        credentials: 'include', // Include cookies in the request
      });
      if (!response.ok) throw new Error('로그아웃 처리 중 오류가 발생했습니다.');
      setIsLoggedIn(false);
      setUser(null);
      setMessage('로그아웃되었습니다.');
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">소셜 로그인 테스트</h1>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">에러:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      {message && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <span className="block sm:inline">{message}</span>
        </div>
      )}
      {!isLoggedIn ? (
        <div className="space-x-2">
          <button onClick={() => handleSocialLogin('google')} className="bg-red-500 text-white px-4 py-2 rounded">
            Google 로그인
          </button>
          <button onClick={() => handleSocialLogin('naver')} className="bg-green-500 text-white px-4 py-2 rounded">
            Naver 로그인
          </button>
          <button onClick={() => handleSocialLogin('kakao')} className="bg-yellow-500 text-white px-4 py-2 rounded">
            Kakao 로그인
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <p>로그인 되었습니다.</p>
          {user && (
            <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative mb-4">
              <p><strong>이름:</strong> {user.name}</p>
              <p><strong>이메일:</strong> {user.email}</p>
            </div>
          )}
          <button onClick={handleLogout} className="bg-gray-500 text-white px-4 py-2 rounded">
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
};

const OAuthCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const provider = localStorage.getItem('oauthProvider');

      if (!code || !state || !provider) {
        console.error('Missing OAuth parameters in callback.');
        navigate('/', { state: { error: 'Invalid OAuth callback parameters.' } });
        return;
      }

      try {
        const url = `${API_BASE_URL}/users/auth/${provider}/callback?state=${state}&code=${code}`;
        const response = await fetch(url, { credentials: 'include' });
        if (!response.ok) throw new Error('Failed to complete OAuth process.');
        navigate('/', { state: { message: 'Login successful.' } });
      } catch (error) {
        console.error('Error in handleOAuthCallback:', error);
        navigate('/', { state: { error: error.message } });
      } finally {
        localStorage.removeItem('oauthProvider');
      }
    };
    handleOAuthCallback();
  }, [location, navigate]);

  return <div>Processing login...</div>;
};

export default App;