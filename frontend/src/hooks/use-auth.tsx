/**
 * Auth context — manages JWT token and current user across the app.
 *
 * Stores the JWT in localStorage. On mount, validates the token by
 * calling GET /auth/me and hydrates the user state.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/services/auth";
import * as authService from "@/services/auth";

const TOKEN_KEY = "cypherpilot-token";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
    displayName?: string,
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });
  const [isLoading, setIsLoading] = useState(true);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    authService
      .getMe()
      .then((u) => {
        setUser(u);
        setIsLoading(false);
      })
      .catch(() => {
        // Token is invalid/expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setIsLoading(false);
      });
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    const result = await authService.login({ username, password });
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
    setUser(result.user);
  }, []);

  const registerFn = useCallback(
    async (
      username: string,
      email: string,
      password: string,
      displayName?: string,
    ) => {
      const result = await authService.register({
        username,
        email,
        password,
        display_name: displayName,
      });
      localStorage.setItem(TOKEN_KEY, result.access_token);
      setToken(result.access_token);
      setUser(result.user);
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const u = await authService.getMe();
      setUser(u);
    } catch {
      // Token expired
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    }
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: !!user,
      isLoading,
      login,
      register: registerFn,
      logout,
      refreshUser,
    }),
    [user, token, isLoading, login, registerFn, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
