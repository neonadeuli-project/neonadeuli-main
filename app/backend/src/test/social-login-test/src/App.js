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
    })();

    return refreshPromise.current;
  }, []);

  const fetchUserInfo = useCallback(async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/info`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log(response.json());
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        throw new Error('사용자 정보를 가져오는데 실패했습니다.');
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      setError(error.message);
    }
  }, []);

  const checkAuthStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        console.log('User loaded from localStorage:', parsedUser);  // 디버깅용 로그
      }
      const token = await refreshAccessToken();
      if (token) {
        await fetchUserInfo(token);
      } else if (!storedUser) {
        setUser(null);
        console.log('No token and no stored user');  // 디버깅용 로그
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setError('인증 상태 확인 중 오류가 발생했습니다.');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [refreshAccessToken, fetchUserInfo]);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/users/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('로그인 실패:', error);
    } finally {
      setAccessToken(null);
      setUser(null);
      localStorage.removeItem('user');
    }
  }, []);

  return { user, setUser, accessToken, isLoading, error, refreshAccessToken, logout, checkAuthStatus };
};

const AuthProvider = ({ children }) => {
  const auth = useAuth();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/auth/:provider/callback" element={<OAuthCallback />} />
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

const Dashboard = () => {
  const { user, isLoading, error, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    const checkUserStatus = () => {
      const storedUser = localStorage.getItem('user');
      console.log('Stored user:', storedUser);  // 디버깅용 로그

      if (!isLoading && !user && !storedUser) {
        console.log('No user found, redirecting to home');  // 디버깅용 로그
        navigate('/');
      }
    };

    checkUserStatus();
  }, [user, isLoading, navigate]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  const userData = user || JSON.parse(localStorage.getItem('user'));

  if (!userData) {
    return null;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <UserInfo user={userData} onLogout={logout} />
    </div>
  );
};


const Home = () => {
  const { user, isLoading, error, checkAuthStatus } = useContext(AuthContext);
  const [message, setMessage] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.state?.message) {
      setMessage(location.state.message);
    }
    checkAuthStatus();
  }, [location, checkAuthStatus]);

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
  const { setUser, refreshAccessToken, checkAuthStatus } = useContext(AuthContext);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const provider = location.pathname.split('/').pop();

      if (!code || !state || !provider) {
        console.error('Missing OAuth parameters in callback.');
        navigate('/', { state: { error: 'Invalid OAuth callback parameters.' } });
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/users/auth/${provider}/callback?state=${state}&code=${code}`, {
          method: 'GET',
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Received user data:', data);  // 디버깅용 로그
          
          if (data.user) {
            setUser(data.user);
            localStorage.setItem('user', JSON.stringify(data.user));
            console.log('User data stored in localStorage');  // 디버깅용 로그
          } else {
            console.error('User data not found in response');
          }

          await refreshAccessToken();
          await checkAuthStatus();
          
          console.log('Navigating to dashboard');  // 디버깅용 로그
          navigate('/dashboard', { state: { message: 'Login successful.' } });
        } else {
          throw new Error('Failed to authenticate');
        }
      } catch (error) {
        console.error('Error in handleOAuthCallback:', error);
        navigate('/', { state: { error: error.message } });
      }
    };

    handleOAuthCallback();
  }, [location, navigate, setUser, refreshAccessToken, checkAuthStatus]);

  return <div>Processing login...</div>;
};

const ErrorMessage = ({ message }) => (
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
    <strong className="font-bold">에러:</strong>
    <span className="block sm:inline"> {message}</span>
  </div>
);

const SuccessMessage = ({ message }) => (
  <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
    <span className="block sm:inline">{message}</span>
  </div>
);

const LoginButtons = ({ onLogin }) => (
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
);

const UserInfo = ({ user, onLogout }) => (
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
);

export default App;