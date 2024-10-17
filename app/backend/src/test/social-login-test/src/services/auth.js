export const storeTokens = (accessToken, refreshToken) => {
    try {
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      console.log('Tokens stored successfully in localStorage.');
    } catch (error) {
      console.error('Failed to store tokens:', error);
    }
  };

export const getAccessToken = () => {
    return localStorage.getItem('accessToken');
};

export const getRefreshToken = () => {
    return localStorage.getItem('refreshToken');
};

export const removeTokens = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
};