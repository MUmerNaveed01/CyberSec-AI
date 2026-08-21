'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { apiClient, API_ROUTES } from '@/lib/api';
import { User, AuthTokens, LoginRequest, RegisterRequest } from '@/types';

interface AuthContextType {
  user: User | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const handleTokensAndUser = useCallback((newTokens: AuthTokens, newUser: User) => {
    setTokens(newTokens);
    setUser(newUser);
    Cookies.set('access_token', newTokens.access_token, { expires: 1 / 96, sameSite: 'lax' }); // 15 mins
    Cookies.set('refresh_token', newTokens.refresh_token, { expires: 7, sameSite: 'lax' }); // 7 days
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(newUser));
    }
  }, []);

  const clearAuth = useCallback(() => {
    setUser(null);
    setTokens(null);
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user');
    }
  }, []);

  // Initialize Auth state
  useEffect(() => {
    const initAuth = async () => {
      const accessToken = Cookies.get('access_token');
      const refreshToken = Cookies.get('refresh_token');
      const storedUser = typeof window !== 'undefined' ? localStorage.getItem('user') : null;

      if (accessToken && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
          setTokens({
            access_token: accessToken,
            refresh_token: refreshToken || '',
            token_type: 'bearer',
          });
          // Verify with /me
          const response = await apiClient.get<User>(API_ROUTES.AUTH.ME);
          setUser(response.data);
          if (typeof window !== 'undefined') {
            localStorage.setItem('user', JSON.stringify(response.data));
          }
        } catch {
          // If token expired, try refresh
          if (refreshToken) {
            try {
              const refreshRes = await apiClient.post<{
                access_token: string;
                refresh_token: string;
                token_type: string;
                user: User;
              }>(API_ROUTES.AUTH.REFRESH, { refresh_token: refreshToken });

              handleTokensAndUser(
                {
                  access_token: refreshRes.data.access_token,
                  refresh_token: refreshRes.data.refresh_token,
                  token_type: refreshRes.data.token_type,
                },
                refreshRes.data.user
              );
            } catch {
              clearAuth();
            }
          } else {
            clearAuth();
          }
        }
      } else if (refreshToken) {
        try {
          const refreshRes = await apiClient.post<{
            access_token: string;
            refresh_token: string;
            token_type: string;
            user: User;
          }>(API_ROUTES.AUTH.REFRESH, { refresh_token: refreshToken });

          handleTokensAndUser(
            {
              access_token: refreshRes.data.access_token,
              refresh_token: refreshRes.data.refresh_token,
              token_type: refreshRes.data.token_type,
            },
            refreshRes.data.user
          );
        } catch {
          clearAuth();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [handleTokensAndUser, clearAuth]);

  const login = async (data: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        user: User;
      }>(API_ROUTES.AUTH.LOGIN, data);

      handleTokensAndUser(
        {
          access_token: response.data.access_token,
          refresh_token: response.data.refresh_token,
          token_type: response.data.token_type,
        },
        response.data.user
      );
      router.push('/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        user: User;
      }>(API_ROUTES.AUTH.REGISTER, data);

      handleTokensAndUser(
        {
          access_token: response.data.access_token,
          refresh_token: response.data.refresh_token,
          token_type: response.data.token_type,
        },
        response.data.user
      );
      router.push('/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.post(API_ROUTES.AUTH.LOGOUT);
    } catch {
      // ignore network errors on logout
    } finally {
      clearAuth();
      router.push('/login');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tokens,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
