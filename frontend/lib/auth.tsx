"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiError, clearTokens, getTokens, setTokens } from "@/lib/api-client";
import type { Me, TokenPair } from "@/lib/types";

interface AuthState {
  user: Me | null;
  loading: boolean;
  authenticated: boolean;
  can: (permission: string) => boolean;
  hasRole: (...roles: string[]) => boolean;
  login: (email: string, password: string) => Promise<Me>;
  register: (data: {
    organization_name?: string;
    full_name: string;
    email: string;
    password: string;
  }) => Promise<Me>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

function readTokens(): TokenPair | null {
  const { access, refresh } = getTokens();
  if (!access || !refresh) return null;
  return { access_token: access, refresh_token: refresh, token_type: "bearer" };
}

function setSessionCookie(): void {
  document.cookie = "sms_session=1; path=/; max-age=604800; samesite=lax";
}

function clearSessionCookie(): void {
  document.cookie = "sms_session=1; path=/; max-age=0";
}

async function fetchMe(): Promise<Me> {
  const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/me`, {
    headers: { Authorization: `Bearer ${getTokens().access}` },
    cache: "no-store",
  });
  if (!resp.ok) throw new ApiError(resp.status, "ME_FAILED", "Failed to load profile");
  return (await resp.json()) as Me;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!readTokens()) {
        setLoading(false);
        return;
      }
      try {
        const me = await fetchMe();
        if (!cancelled) setUser(me);
      } catch {
        clearTokens();
        clearSessionCookie();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const applyTokens = useCallback((tokens: TokenPair) => {
    setTokens(tokens.access_token, tokens.refresh_token);
    setSessionCookie();
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
          cache: "no-store",
        },
      ).then(async (resp) => {
        const body = await resp.json();
        if (!resp.ok) throw new ApiError(resp.status, body?.error?.code ?? "LOGIN_FAILED", body?.error?.message ?? "Login failed");
        return body as TokenPair;
      });
      applyTokens(tokens);
      const me = await fetchMe();
      setUser(me);
      return me;
    },
    [applyTokens],
  );

  const register = useCallback(
    async (data: { organization_name?: string; full_name: string; email: string; password: string }) => {
      const tokens = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/register`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
          cache: "no-store",
        },
      ).then(async (resp) => {
        const body = await resp.json();
        if (!resp.ok) throw new ApiError(resp.status, body?.error?.code ?? "REGISTER_FAILED", body?.error?.message ?? "Registration failed");
        return body as TokenPair;
      });
      applyTokens(tokens);
      const me = await fetchMe();
      setUser(me);
      return me;
    },
    [applyTokens],
  );

  const logout = useCallback(async () => {
    const { refresh } = getTokens();
    if (refresh) {
      try {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/logout`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refresh }),
            cache: "no-store",
          },
        );
      } catch {
        // ignore network errors on logout
      }
    }
    clearTokens();
    clearSessionCookie();
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      authenticated: user !== null,
      can: (permission) => user?.permissions.includes(permission) ?? false,
      hasRole: (...roles) => user?.roles.some((r) => roles.includes(r.code)) ?? false,
      login,
      register,
      logout,
    }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}