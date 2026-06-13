/**
 * Auth client - using frontend proxy for auth requests
 * This ensures browser requests work properly with same-origin policy
 */

// Use frontend proxy endpoint for auth (always available from browser)
const AUTH_URL = "/api/backend/auth/token";

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
    const response = await fetch(AUTH_URL, {
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
