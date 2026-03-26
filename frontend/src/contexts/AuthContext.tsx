"use client";

/**
 * Authentication context provider for the admin panel.
 *
 * Manages JWT token lifecycle, user state, and role-based access.
 * Wraps admin pages to provide login/logout and auth guard.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import {
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  decodeToken,
  isTokenExpired,
} from "@/lib/auth";
import { loginWithCredentials, fetchCurrentUser } from "@/lib/admin-api";
import type { UserRole, UserInfo } from "@/types/api";

interface AuthState {
  user: UserInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STAFF_ROLES: UserRole[] = ["admin", "staff"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  });

  // Check for existing token on mount
  useEffect(() => {
    const token = getAccessToken();
    if (token && !isTokenExpired(token)) {
      const payload = decodeToken(token);
      if (payload) {
        // Fetch full user info from API
        fetchCurrentUser()
          .then((user) => {
            setState({
              user,
              isLoading: false,
              isAuthenticated: true,
              error: null,
            });
          })
          .catch(() => {
            clearAccessToken();
            setState({
              user: null,
              isLoading: false,
              isAuthenticated: false,
              error: null,
            });
          });
        return;
      }
    }
    setState((prev) => ({ ...prev, isLoading: false }));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await loginWithCredentials(email, password);
      setAccessToken(response.access_token);

      const user = await fetchCurrentUser();

      // Only staff and admin can access the admin panel
      if (!STAFF_ROLES.includes(user.role)) {
        clearAccessToken();
        setState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: "Access denied. Staff or admin role required.",
        });
        return;
      }

      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      });
    } catch (err) {
      clearAccessToken();
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: err instanceof Error ? err.message : "Login failed",
      });
    }
  }, []);

  const logout = useCallback(() => {
    clearAccessToken();
    setState({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
    });
  }, []);

  const hasRole = useCallback(
    (roles: UserRole[]) => {
      if (!state.user) return false;
      return roles.includes(state.user.role);
    },
    [state.user]
  );

  const value = useMemo(
    () => ({
      ...state,
      login,
      logout,
      hasRole,
    }),
    [state, login, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
