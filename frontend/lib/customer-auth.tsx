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

import { ApiError } from "@/lib/api-client";
import { sfPath } from "@/lib/storefront-slug";
import type {
  CustomerMe,
  CustomerProfileUpdate,
  CustomerRegisterInput,
  CustomerTokenPair,
} from "@/lib/types";

const CUSTOMER_ACCESS_KEY = "sms_customer_access";
const CUSTOMER_REFRESH_KEY = "sms_customer_refresh";
const CART_TOKEN_KEY = "sms_cart_token";
const WISHLIST_TOKEN_KEY = "sms_wishlist_token";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function getCustomerTokens(): { access: string | null; refresh: string | null } {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: localStorage.getItem(CUSTOMER_ACCESS_KEY),
    refresh: localStorage.getItem(CUSTOMER_REFRESH_KEY),
  };
}

export function setCustomerTokens(access: string, refresh: string): void {
  localStorage.setItem(CUSTOMER_ACCESS_KEY, access);
  localStorage.setItem(CUSTOMER_REFRESH_KEY, refresh);
}

export function clearCustomerTokens(): void {
  localStorage.removeItem(CUSTOMER_ACCESS_KEY);
  localStorage.removeItem(CUSTOMER_REFRESH_KEY);
}

export function getCartToken(): string {
  if (typeof window === "undefined") return "";
  let token = localStorage.getItem(CART_TOKEN_KEY);
  if (!token) {
    token = window.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(CART_TOKEN_KEY, token);
  }
  return token;
}

export function getWishlistToken(): string {
  if (typeof window === "undefined") return "";
  let token = localStorage.getItem(WISHLIST_TOKEN_KEY);
  if (!token) {
    token = window.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(WISHLIST_TOKEN_KEY, token);
  }
  return token;
}

/** Headers identifying the shopper: customer JWT when logged in, else guest cart token. */
export function cartHeaders(): Record<string, string> {
  const { access } = getCustomerTokens();
  const headers: Record<string, string> = { "X-Cart-Token": getCartToken() };
  if (access) headers.Authorization = `Bearer ${access}`;
  return headers;
}

/** Headers for wishlist endpoints: customer JWT or guest wishlist token. */
export function wishlistHeaders(): Record<string, string> {
  const { access } = getCustomerTokens();
  const headers: Record<string, string> = { "X-Wishlist-Token": getWishlistToken() };
  if (access) headers.Authorization = `Bearer ${access}`;
  return headers;
}

async function parseError(resp: Response): Promise<ApiError> {
  let code = "UNKNOWN_ERROR";
  let message = "Something went wrong";
  try {
    const body = await resp.json();
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
    }
  } catch {
    // non-JSON error body
  }
  return new ApiError(resp.status, code, message);
}

/** Fetch against a storefront endpoint with customer auth + guest cart token. */
export async function customerRequest<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    headers?: Record<string, string>;
  } = {},
): Promise<T> {
  const { access, refresh } = getCustomerTokens();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...cartHeaders(),
    ...wishlistHeaders(),
    ...options.headers,
  };
  if (access) headers.Authorization = `Bearer ${access}`;

  let resp = await fetch(API_URL + path, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (resp.status === 401 && refresh) {
    try {
      const rotated = await fetch(API_URL + path.replace(/\/[^/]+$/, "") + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
        cache: "no-store",
      });
      if (rotated.ok) {
        const body = (await rotated.json()) as CustomerTokenPair;
        setCustomerTokens(body.access_token, body.refresh_token);
        headers.Authorization = `Bearer ${body.access_token}`;
        resp = await fetch(API_URL + path, {
          method: options.method ?? "GET",
          headers,
          body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
          cache: "no-store",
        });
      } else {
        clearCustomerTokens();
      }
    } catch {
      clearCustomerTokens();
    }
  }

  if (!resp.ok) throw await parseError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

interface CustomerAuthState {
  customer: CustomerMe | null;
  loading: boolean;
  authenticated: boolean;
  login: (email: string, password: string) => Promise<CustomerMe>;
  register: (data: CustomerRegisterInput) => Promise<CustomerMe>;
  logout: () => Promise<void>;
  updateProfile: (data: CustomerProfileUpdate) => Promise<CustomerMe>;
  refreshProfile: () => Promise<CustomerMe | null>;
}

const CustomerAuthContext = createContext<CustomerAuthState | null>(null);

async function fetchCustomerMe(): Promise<CustomerMe> {
  const path = await sfPath("/auth/me");
  return customerRequest<CustomerMe>(path);
}

export function CustomerAuthProvider({ children }: { children: ReactNode }) {
  const [customer, setCustomer] = useState<CustomerMe | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const tokens = getCustomerTokens();
    if (!tokens.access || !tokens.refresh) return null;
    try {
      const me = await fetchCustomerMe();
      setCustomer(me);
      return me;
    } catch {
      clearCustomerTokens();
      setCustomer(null);
      return null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const tokens = getCustomerTokens();
      if (!tokens.access || !tokens.refresh) {
        setLoading(false);
        return;
      }
      try {
        const me = await fetchCustomerMe();
        if (!cancelled) setCustomer(me);
      } catch {
        clearCustomerTokens();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const path = await sfPath("/auth/login");
    const tokens = await customerRequest<CustomerTokenPair>(path, {
      method: "POST",
      body: { email, password },
    });
    setCustomerTokens(tokens.access_token, tokens.refresh_token);
    const me = await fetchCustomerMe();
    setCustomer(me);
    return me;
  }, []);

  const register = useCallback(async (data: CustomerRegisterInput) => {
    const path = await sfPath("/auth/register");
    const tokens = await customerRequest<CustomerTokenPair>(path, {
      method: "POST",
      body: data,
    });
    setCustomerTokens(tokens.access_token, tokens.refresh_token);
    const me = await fetchCustomerMe();
    setCustomer(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    const { refresh } = getCustomerTokens();
    if (refresh) {
      try {
        const path = await sfPath("/auth/logout");
        await customerRequest<void>(path, {
          method: "POST",
          body: { refresh_token: refresh },
        });
      } catch {
        // ignore network errors on logout
      }
    }
    clearCustomerTokens();
    setCustomer(null);
  }, []);

  const updateProfile = useCallback(async (data: CustomerProfileUpdate) => {
    const path = await sfPath("/auth/me");
    const me = await customerRequest<CustomerMe>(path, { method: "PATCH", body: data });
    setCustomer(me);
    return me;
  }, []);

  const value = useMemo<CustomerAuthState>(
    () => ({ customer, loading, authenticated: customer !== null, login, register, logout, updateProfile, refreshProfile }),
    [customer, loading, login, register, logout, updateProfile, refreshProfile],
  );

  return <CustomerAuthContext.Provider value={value}>{children}</CustomerAuthContext.Provider>;
}

export function useCustomerAuth(): CustomerAuthState {
  const ctx = useContext(CustomerAuthContext);
  if (!ctx) throw new Error("useCustomerAuth must be used within CustomerAuthProvider");
  return ctx;
}