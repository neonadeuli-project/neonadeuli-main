import React, { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation, useNavigate, Navigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const AuthContext = createContext(null);

const useAuth = () => {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const refreshPromise = useRef(null);

  const refreshAccessToken = useCallback(async () => {
    if (refreshPromise.current) {
      return refreshPromise.current;
    }

    refreshPromise.current = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/token/refresh`, {
          method: 'POST',
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setAccessToken(data.access_token);
          return data.access_token;
        } else if (response.status === 401) {
          // 로그인하지 않은 상태와 인증 만료를 구분
          const errorData = await response.json();
          if (errorData.detail === "Refresh Token이 일치하지 않습니다.") {
            // 로그인하지 않은 상태
            setUser(null);
            setAccessToken(null);
            return null; // 에러를 던지지 않고 null 반환
          } else {
            // 인증 만료
            setUser(null);
            setAccessToken(null);
            throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
          }
        }
        throw new Error('토큰 갱신에 실패했습니다.');
      } catch (error) {
        if (error.message !== '인증이 만료되었습니다. 다시 로그인해주세요.') {
          console.error('Failed to refresh token:', error);
        }
        setError(error.message);
        throw error;
      } finally {
        refreshPromise.current = null;
      }
    });

    return refreshPromise.current;
  }, []);

  const fetchUserInfo = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/info`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '사용자 정보를 가져오는데 실패했습니다.');
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      setUser(null);
      localStorage.removeItem('user');
      setError(error.message);
    }
  }, []);

  const checkAuthStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const storedUser = localStorage.getItem('user');
      
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      } else {
        // 토큰이 없으면 서버에 사용자 정보 요청
        const response = await fetch(`${API_BASE_URL}/users/info`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setUser(data);
          localStorage.setItem('user', JSON.stringify(data));
        } else {
          setUser(null);
          localStorage.removeItem('user');
        }
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setError('인증 상태 확인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('Checking auth status');
    checkAuthStatus();
  }, [checkAuthStatus]);

  const logout = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        setAccessToken(null);
        setUser(null);
        localStorage.removeItem('user');
      }
    } catch (error) {
      console.error('로그인 실패:', error);
    } 
  }, [setAccessToken, setUser]);

  return { user, setUser, accessToken, setAccessToken, isLoading, error, setError, fetchUserInfo, refreshAccessToken, logout, checkAuthStatus };
};

const AuthProvider = ({ children }) => {
  const auth = useAuth();
  useEffect(() => {
    // Function to check if the access token is nearing expiration and refresh it
    const autoRefreshToken = async () => {
      const expirationTime = localStorage.getItem('accessTokenExpiration');
      const currentTime = new Date().getTime();
      if (expirationTime && currentTime >= expirationTime) {
        await auth.refreshAccessToken(); // Use the refresh function from the auth context
      }
    };

    // Setup interval or check before every API call
    const intervalId = setInterval(autoRefreshToken, 5 * 60 * 1000); // Check every 5 minutes

    return () => clearInterval(intervalId);
  }, [auth]);

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/auth/:provider/callback" element={<OAuthCallback />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<Home />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

const Dashboard = () => {
  const { user, isLoading, error, logout, checkAuthStatus, setUser, setAccessToken, setError } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    const verifyAuth = async () => {
      await checkAuthStatus();
    };
    verifyAuth();
  }, [checkAuthStatus]); // 빈 의존성 배열

  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/');
    }
  }, [user, isLoading, navigate]);

  const handleRefreshToken = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/token/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setAccessToken(data.access_token);
        localStorage.setItem('accessToken', data.access_token);
        await checkAuthStatus(); // 사용자 정보 업데이트
      } else {
        const errorData = await response.json();
        if (response.status === 401) {
          // Handle when the refresh token is expired or doesn't match
          setUser(null);
          localStorage.removeItem('user');
          navigate('/');  // Redirect user to login page
          throw new Error(errorData.detail || '로그인이 만료되었습니다. 다시 로그인해주세요.');
        } else {
          throw new Error(errorData.detail || '토큰 갱신에 실패했습니다.');
        }
      }
    } catch (error) {
      console.error('토큰 갱신 실패:', error);
      setError(error.message);
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return null;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <UserInfo user={user} onLogout={logout} />
      <button onClick={handleRefreshToken} className="bg-blue-500 text-white px-4 py-2 rounded mt-4">
        토큰 갱신
      </button>
    </div>
  );
};

const Home = () => {
  const { user, isLoading, error } = useContext(AuthContext);
  const [message, setMessage] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.state?.message) {
      setMessage(location.state.message);
    }
  }, [location]);

  useEffect(() => {
    if (!isLoading && user) {
      navigate('/dashboard');
    }
  }, [user, isLoading, navigate]);

  const handleSocialLogin = async (provider) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/login/${provider}`);
      const data = await response.json();
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        throw new Error('인증 URL이 제공되지 않았습니다.');
      }
    } catch (error) {
      console.error('로그인 초기화 중 오류 발생:', error);
      setMessage(error.message || '로그인 프로세스 중 오류가 발생했습니다.');
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">소셜 로그인 테스트</h1>
      {error && <ErrorMessage message={error} />}
      {message && <SuccessMessage message={message} />}
      {!user ? (
        <LoginButtons onLogin={handleSocialLogin} />
      ) : (
        <Navigate to="/dashboard" replace />
      )}
    </div>
  );
};

const OAuthCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useContext(AuthContext);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const userParam = params.get('user');

    if (userParam) {
      const user = JSON.parse(decodeURIComponent(userParam));
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      navigate('/dashboard');
    } else {
      console.error('User data or access token not found in URL');
      navigate('/');
    }
  }, [location, navigate, setUser]);

  return <div>Processing login...</div>;
};

const ErrorMessage = React.memo(({ message }) => (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
    <strong className="font-bold">에러:</strong>
    <span className="block sm:inline"> {message}</span>
  </div>
));

const SuccessMessage = React.memo(({ message }) => (
  <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
    <span className="block sm:inline">{message}</span>
  </div>
));

const LoginButtons = React.memo(({ onLogin }) => (
  <div className="space-x-2">
    <button onClick={() => onLogin('google')} className="bg-red-500 text-white px-4 py-2 rounded">
      Google 로그인
    </button>
    <button onClick={() => onLogin('naver')} className="bg-green-500 text-white px-4 py-2 rounded">
      Naver 로그인
    </button>
    <button onClick={() => onLogin('kakao')} className="bg-yellow-500 text-white px-4 py-2 rounded">
      Kakao 로그인
    </button>
  </div>
));

const UserInfo = React.memo(({ user, onLogout }) => (
  <div className="space-y-2">
    <p>로그인 되었습니다.</p>
    <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative mb-4">
      <p><strong>이름:</strong> {user.name}</p>
      <p><strong>이메일:</strong> {user.email}</p>
    </div>
    <button onClick={onLogout} className="bg-gray-500 text-white px-4 py-2 rounded">
      로그아웃
    </button>
  </div>
));

export default App;