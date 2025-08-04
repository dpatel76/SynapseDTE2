import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole, LoginRequest } from '../types/api';
import { authApi } from '../api/auth';
import { usersApi } from '../api/users';

interface AuthContextType {
  user: User | null;
  impersonatedUser: User | null;
  isImpersonating: boolean;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  impersonateUser: (userId: number) => Promise<void>;
  stopImpersonation: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [impersonatedUser, setImpersonatedUser] = useState<User | null>(null);
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check for existing auth token and user data
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        
        console.log('InitAuth - token:', token);
        console.log('InitAuth - storedUser:', storedUser);
        
        if (token && storedUser) {
          try {
            const userData = JSON.parse(storedUser);
            console.log('Parsed user data:', userData);
            console.log('User role from storage:', userData.role);
            setUser(userData);
          } catch {
            // Invalid stored user data
            console.log('Invalid stored user data, clearing localStorage');
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
          }
        } else {
          console.log('No token or user data found');
          setUser(null);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      console.log('AuthContext login called with:', credentials);
      const response = await authApi.login(credentials);
      
      console.log('Login response:', response);
      console.log('User data from response:', response.user);
      console.log('User role from response:', response.user?.role);
      
      // Store auth data
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      
      console.log('Token stored:', localStorage.getItem('token'));
      console.log('User stored:', localStorage.getItem('user'));
      
      // Update state
      setUser(response.user);
      
      console.log('User set in state:', response.user);
    } catch (error) {
      console.error('Login error in AuthContext:', error);
      // Clear any existing auth data
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.warn('Logout API error:', error);
    } finally {
      // Always clear local storage and state
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('impersonation_token');
      setUser(null);
      setImpersonatedUser(null);
      setIsImpersonating(false);
    }
  };

  const impersonateUser = async (userId: number) => {
    if (user?.role !== UserRole.ADMIN) {
      throw new Error('Only admin users can impersonate');
    }

    const response = await usersApi.impersonate(userId);
    localStorage.setItem('impersonation_token', response.access_token);
    setImpersonatedUser(response.impersonated_user);
    setIsImpersonating(true);
  };

  const stopImpersonation = async () => {
    localStorage.removeItem('impersonation_token');
    setImpersonatedUser(null);
    setIsImpersonating(false);
  };

  return (
    <AuthContext.Provider value={{
      user,
      impersonatedUser,
      isImpersonating,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      impersonateUser,
      stopImpersonation
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 