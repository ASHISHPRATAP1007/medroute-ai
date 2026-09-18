import { apiRequest, clearTokens, getRefreshToken, setTokens } from "@/lib/api-client";

export async function registerMR(payload) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
}

export async function login(email, password) {
  const body = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    skipAuth: true,
  });
  setTokens(body.data);
  return body.data;
}

export async function logout() {
  const refreshToken = getRefreshToken();
  try {
    if (refreshToken) {
      await apiRequest("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    }
  } finally {
    clearTokens();
  }
}

export async function getCurrentUser() {
  const body = await apiRequest("/auth/me");
  return body.data;
}
