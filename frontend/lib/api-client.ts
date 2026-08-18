export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown> | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface ListQuery {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  [key: string]: string | number | undefined;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_KEY = "sms_access_token";
const REFRESH_KEY = "sms_refresh_token";

export function getTokens(): { access: string | null; refresh: string | null } {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: localStorage.getItem(ACCESS_KEY),
    refresh: localStorage.getItem(REFRESH_KEY),
  };
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

function buildUrl(path: string, query?: ListQuery): string {
  const url = new URL(API_URL + path);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseError(resp: Response): Promise<ApiError> {
  let code = "UNKNOWN_ERROR";
  let message = "Something went wrong";
  let details: Record<string, unknown> | null = null;
  try {
    const body = await resp.json();
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
      details = body.error.details ?? null;
    }
  } catch {
    // non-JSON error body
  }
  return new ApiError(resp.status, code, message, details);
}

async function rawRequest(
  path: string,
  options: { method?: string; body?: unknown; query?: ListQuery; headers?: Record<string, string> } = {},
  token: string | null,
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(buildUrl(path, options.query), {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });
  if (resp.status === 204) return resp;
  return resp;
}

async function refreshAccess(refresh: string): Promise<string> {
  const resp = await fetch(buildUrl("/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
    cache: "no-store",
  });
  if (!resp.ok) throw new ApiError(resp.status, "TOKEN_EXPIRED", "Session expired");
  const body = await resp.json();
  setTokens(body.access_token, body.refresh_token);
  return body.access_token;
}

export async function apiRequest<T>(
  path: string,
  options: { method?: string; body?: unknown; query?: ListQuery; headers?: Record<string, string> } = {},
): Promise<T> {
  const { access, refresh } = getTokens();

  let resp = await rawRequest(path, options, access);

  if (resp.status === 401 && refresh) {
    try {
      const newAccess = await refreshAccess(refresh);
      resp = await rawRequest(path, options, newAccess);
    } catch (err) {
      clearTokens();
      if (err instanceof ApiError && err.code === "TOKEN_EXPIRED") throw err;
      throw new ApiError(401, "TOKEN_EXPIRED", "Session expired");
    }
  }

  if (!resp.ok) throw await parseError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  get: <T>(path: string, query?: ListQuery) => apiRequest<T>(path, { query }),
  post: <T>(path: string, body?: unknown, headers?: Record<string, string>) =>
    apiRequest<T>(path, { method: "POST", body, headers }),
  put: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "PATCH", body }),
  delete: (path: string) => apiRequest<void>(path, { method: "DELETE" }),
};