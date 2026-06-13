/**
 * Auth client - now using FastAPI JWT backend
 * This is a simple API client for authentication
 */

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

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authClient = {
  /**
   * Login with username and password
   * Returns JWT token
   */
  async login(username: string, password: string): Promise<AuthResponse> {
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
      const error = await response.json();
      throw new Error(error.detail || "Authentication failed");
    }

    return response.json();
  },

  /**
   * Get authorization header for authenticated requests
   */
  getAuthHeader(): Record<string, string> {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return typeof window !== "undefined" && !!localStorage.getItem("auth_token");
  },

  /**
   * Clear authentication
   */
  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
  },
};
