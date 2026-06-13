"use client";

import { User } from "@/lib/types";
import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";
const API_URL = (() => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}${API_BASE}`
    : process.env.NEXT_PUBLIC_API_V1_URL || "http://localhost:8000/api/v1";

  if (typeof window === "undefined") {
    return apiUrl;
  }

  try {
    const url = new URL(apiUrl);
    if (url.hostname === "backend") {
      return `${window.location.protocol}//${window.location.hostname}:8000${url.pathname}`;
    }
  } catch {
    // Ignore invalid URL and use resolved apiUrl
  }

  return apiUrl;
})();

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session from localStorage on mount
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedToken = localStorage.getItem("auth_token");
        const savedUser = localStorage.getItem("auth_user");

        if (savedToken && savedUser) {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        }
      } catch (err) {
        console.error("Failed to restore session:", err);
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  // Login with username and password
  const login = async (username: string, password: string) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/auth/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username,
          password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      const data = await response.json();
      const { access_token } = data;

      // Store token in localStorage and cookie
      localStorage.setItem("auth_token", access_token);
      // Set cookie for middleware to detect auth state
      document.cookie = `auth_token=${access_token}; path=/; max-age=86400`; // 24 hours

      // Create user object from username
      const userData: User = {
        id: username,
        email: `${username}@pharmaviyum.local`,
        name: username,
        avatar: "",
        role: "user",
      };

      localStorage.setItem("auth_user", JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Login failed";
      setError(errorMessage);
      throw err;
    }
  };

  // Logout
  const logout = async () => {
    try {
      // Clear token from localStorage and cookie
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      // Clear cookie
      document.cookie = "auth_token=; path=/; max-age=0";
      setToken(null);
      setUser(null);
      setError(null);
    } catch (err) {
      console.error("Logout failed:", err);
      setUser(null);
      setToken(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user && !!token,
        isLoading,
        token,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
