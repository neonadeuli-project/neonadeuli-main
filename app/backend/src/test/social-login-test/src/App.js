import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    const accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
      setIsLoggedIn(true);
      fetchUserInfo(accessToken);
    }
  }, []);

  const fetchUserInfo = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/info`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        throw new Error('사용자 정보를 가져오는데 실패했습니다.');
      }
    } catch (error) {
      setError(error.message);
    }
  };

  const handleSocialLogin = async (provider) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/login/${provider}`);
      const data = await response.json();
      window.location.href = data.auth_url;
    } catch (error) {
      setError('로그인 초기화 중 오류가 발생했습니다.');
    }
  };

  const handleTokenRefresh = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      const response = await fetch(`${API_BASE_URL}/users/token/refresh`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        setMessage('토큰이 성공적으로 갱신되었습니다.');
        fetchUserInfo(data.access_token);
      } else {
        throw new Error('토큰 갱신에 실패했습니다.');
      }
    } catch (error) {
      setError(error.message);
    }
  };

  const handleLogout = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      const response = await fetch(`${API_BASE_URL}/users/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      if (response.ok) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setIsLoggedIn(false);
        setUser(null);
        setMessage('로그아웃되었습니다.');
      } else {
        throw new Error('로그아웃 처리 중 오류가 발생했습니다.');
      }
    } catch (error) {
      setError(error.message);
    }
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const refreshToken = urlParams.get('refresh_token');
    if (accessToken && refreshToken) {
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      setIsLoggedIn(true);
      fetchUserInfo(accessToken);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

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
          <button onClick={handleTokenRefresh} className="bg-blue-500 text-white px-4 py-2 rounded">
            토큰 갱신
          </button>
          <button onClick={handleLogout} className="bg-gray-500 text-white px-4 py-2 rounded">
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
};

export default App;