/**
 * Centralized API client. No component should call fetch() directly —
 * everything goes through here (or the per-domain services that wrap it)
 * per project rule "do not scatter fetch() calls throughout UI components".
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "medroute_access_token";
const REFRESH_TOKEN_KEY = "medroute_refresh_token";

// In-memory storage note: real browsers should use httpOnly cookies for
// refresh tokens in production. For Phase 1 simplicity we keep both in
// memory + sessionStorage; swapping to httpOnly cookies is a Phase 2-safe
// change that doesn't require touching call sites.
export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens({ access_token, refresh_token }) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(ACCESS_TOKEN_KEY, access_token);
  window.sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message, status, errors = []) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new ApiError("No refresh token available.", 401);

  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearTokens();
    throw new ApiError("Your session has expired. Please login again.", 401);
  }

  const body = await res.json();
  setTokens(body.data);
  return body.data.access_token;
}

/**
 * @param {string} path - e.g. "/doctors"
 * @param {RequestInit & { skipAuth?: boolean, skipRefreshRetry?: boolean }} options
 */
export async function apiRequest(path, options = {}) {
  const { skipAuth = false, skipRefreshRetry = false, headers, ...rest } = options;

  const finalHeaders = { "Content-Type": "application/json", ...headers };
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...rest, headers: finalHeaders });
  } catch (networkError) {
    throw new ApiError("Unable to connect to server. Please try again.", 0);
  }

  // Attempt one silent refresh-and-retry on 401 (unless this *is* the refresh call).
  if (res.status === 401 && !skipAuth && !skipRefreshRetry) {
    try {
      const newAccessToken = await refreshAccessToken();
      return apiRequest(path, {
        ...options,
        skipRefreshRetry: true,
        headers: { ...headers, Authorization: `Bearer ${newAccessToken}` },
      });
    } catch {
      throw new ApiError("Your session has expired. Please login again.", 401);
    }
  }

  let body = null;
  try {
    body = await res.json();
  } catch {
    // No JSON body (e.g. 204) — fine.
  }

  if (!res.ok) {
    if (res.status === 403) {
      throw new ApiError(body?.message || "You don't have permission to perform this action.", 403, body?.errors);
    }
    throw new ApiError(body?.message || "Something went wrong.", res.status, body?.errors);
  }

  return body;
}

export { ApiError };
