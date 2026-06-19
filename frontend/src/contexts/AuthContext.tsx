"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (!savedToken) {
      setLoading(false);
      return;
    }

    setToken(savedToken);

    let retries = 0;
    const maxRetries = 3;
    const tryValidate = () => {
      api.user.me()
        .then((u) => {
          setUser(u);
          setLoading(false);
        })
        .catch((err) => {
          if (err?.message?.includes?.("401") || err?.message?.includes?.("Invalid") || err?.message?.includes?.("expired")) {
            localStorage.removeItem("token");
            setToken(null);
            setLoading(false);
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(tryValidate, 2000 * retries);
          } else {
            setUser({ id: 0, email: "", username: savedToken ? "..." : "", full_name: "", is_premium: false, is_active: true } as User);
            setLoading(false);
          }
        });
    };

    tryValidate();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.auth.login({ email, password });
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const register = async (email: string, username: string, password: string) => {
    const res = await api.auth.register({ email, username, password });
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
