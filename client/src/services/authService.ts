/**
 * Authentication Service
 * 
 * Handles authentication-related functionality for the IoT Anomaly Detection System
 */

import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from '@/constants/constants';
import axios from 'axios';

// API base URL - using relative path for proxy
const API_URL = '/api/v1/auth';

// Token storage keys

/**
 * User interface
 */
export interface User {
  id?: string;
  username: string;
  email: string;
  disabled: boolean;
  full_name?: string;
  roles: string[];
}

/**
 * Token response interface
 */
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

/**
 * Login with username and password
 * 
 * @param username User's username
 * @param password User's password
 * @returns Promise with login result
 */
export const login = async (username: string, password: string): Promise<User> => {
  try {
    const response = await axios.post<TokenResponse>(
      `${API_URL}/token`,
      new URLSearchParams({
        username,
        password,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    if (response.data.access_token) {
      // Store tokens and user data
      localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));

      // Set default Authorization header for all future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;

      // Set up token refresh before it expires
      setupTokenRefresh(response.data.expires_in);

      return response.data.user;
    }

    throw new Error('No token received from server');
  } catch (error: any) {
    if (error && error.response) {
      throw new Error(error.response?.data?.detail || 'Authentication failed');
    }
    throw new Error(error?.message || 'Authentication failed');
  }
};

/**
 * Logout the current user
 */
export const logout = (): void => {
  // Remove tokens and user data
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);

  // Remove Authorization header
  delete axios.defaults.headers.common['Authorization'];

  // Clear any refresh timers
  if (window.tokenRefreshTimer) {
    clearTimeout(window.tokenRefreshTimer);
    delete window.tokenRefreshTimer;
  }
};

/**
 * Get the current user
 * 
 * @returns Current user or null if not logged in
 */
export const getCurrentUser = async (): Promise<User | null> => {

  const { data: user } = await axios.get<User>(`${API_URL}/users/me`);

  localStorage.setItem(USER_KEY, JSON.stringify(user));

  if (!user) {
    return null;
  }

  return user;
};

/**
 * Get the current user from local storage
 * 
 * @returns Current user or null if not logged in
 */
export const getCurrentUserFromLocalStorage = (): User | null => {
  const userJson = localStorage.getItem(USER_KEY);

  if (!userJson || userJson === 'undefined') {
    return null;
  }

  return JSON.parse(userJson);
};

/**
 * Get the access token
 * 
 * @returns Access token or null if not logged in
 */
export const getToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * Get the refresh token
 * 
 * @returns Refresh token or null if not logged in
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Check if the user is logged in
 * 
 * @returns True if logged in, false otherwise
 */
export const isLoggedIn = (): boolean => {
  return !!getToken();
};

/**
 * Check if the current user has a specific role
 * 
 * @param role Role to check
 * @returns True if user has the role, false otherwise
 */
export const hasRole = (role: string): boolean => {
  const user = getCurrentUserFromLocalStorage();

  if (!user) {
    return false;
  }

  return user.roles.includes(role);
};

/**
 * Check if the current user is an admin
 * 
 * @returns True if user is an admin, false otherwise
 */
export const isAdmin = (): boolean => {
  return hasRole('admin');
};

/**
 * Refresh the access token using the refresh token
 * 
 * @returns Promise with the new user data or null if refresh failed
 */
export const refreshToken = async (): Promise<User | null> => {
  try {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      return null;
    }

    const response = await axios.post<TokenResponse>(
      `${API_URL}/refresh`,
      { refresh_token: refreshToken },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.data.access_token) {
      // Store new tokens
      localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);

      // Update user data if available
      if (response.data.user) {
        localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      }

      // Update Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;

      // Set up next token refresh
      setupTokenRefresh(response.data.expires_in);

      return response.data.user || getCurrentUserFromLocalStorage();
    }

    return null;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
};

/**
 * Set up automatic token refresh before the access token expires
 * 
 * @param expiresIn Expiration time in seconds
 */
const setupTokenRefresh = (expiresIn: number): void => {
  // Clear any existing timer
  if (window.tokenRefreshTimer) {
    clearTimeout(window.tokenRefreshTimer);
  }

  // Set timer to refresh token before it expires (refresh at 75% of expiry time)
  const refreshTime = Math.max(expiresIn * 0.75, 10) * 1000; // in milliseconds, minimum 10 seconds

  // @ts-ignore - Add the timer to the window object for global access
  window.tokenRefreshTimer = setTimeout(async () => {
    await refreshToken();
  }, refreshTime);
};

/**
 * Initialize authentication from local storage
 * 
 * Call this when the application starts to restore authentication state
 */
export const initAuth = (): void => {
  const token = getToken();
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    // Attempt to refresh the token on initialization
    refreshToken().catch(error => {
      console.error('Failed to refresh token during initialization:', error);
    });
  }
};

/**
 * Authentication service object
 */
const authService = {
  login,
  logout,
  getCurrentUser,
  getCurrentUserFromLocalStorage,
  getToken,
  getRefreshToken,
  refreshToken,
  isLoggedIn,
  hasRole,
  isAdmin,
  initAuth,
};

export default authService;
