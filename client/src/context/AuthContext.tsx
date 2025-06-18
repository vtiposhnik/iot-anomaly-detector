/**
 * Authentication Context
 * 
 * Provides authentication state and functions to the entire application
 */

import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import authService, { User } from '@/services/authService';

/**
 * Authentication context interface
 */
interface AuthContextType {
  loading: boolean;
  error: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: () => boolean;
  isLoggedIn: boolean;
}

// Create the context without a default to detect missing provider usage
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Props for AuthProvider component
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider component
 * 
 * Wraps the application and provides authentication state and functions
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize authentication state from local storage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        authService.initAuth();
        const currentUser = await authService.getCurrentUser();

        setUser(currentUser);
        setIsLoggedIn(!!currentUser);
      } catch (err) {
        console.error('Failed to initialize authentication:', err);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  /**
   * Login function
   * 
   * @param username User's username
   * @param password User's password
   */
  const login = async (username: string, password: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const userData = await authService.login(username, password);
      setUser(userData);
      setIsLoggedIn(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Logout function
   */
  const logout = (): void => {
    authService.logout();
    setUser(null);
    setIsLoggedIn(false);
  };

  /**
   * Check if the current user is an admin
   * 
   * @returns True if user is an admin, false otherwise
   */
  const isAdmin = (): boolean => {
    return authService.isAdmin();
  };

  // Provide the authentication context to children
  return (
    <AuthContext.Provider
      value={{
        loading,
        error,
        user,
        isLoggedIn,
        login,
        logout,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use the authentication context
 * 
 * @returns Authentication context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
