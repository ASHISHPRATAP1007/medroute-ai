"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getAccessToken } from "@/lib/api-client";
import { getCurrentUser, login as loginRequest, logout as logoutRequest } from "@/services/auth-service";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      if (!getAccessToken()) {
        setIsLoading(false);
        return;
      }
      try {
        const current = await getCurrentUser();
        setUser(current);
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap();
  }, []);

  async function login(email, password) {
    await loginRequest(email, password);
    const current = await getCurrentUser();
    setUser(current);
    return current;
  }

  async function logout() {
    await logoutRequest();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
