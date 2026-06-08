/**
 * Server-side session retrieval using FastAPI JWT token from localStorage
 * Note: For production, tokens should be in httpOnly cookies
 */

import { cookies, headers } from "next/headers";

export interface AuthUser {
  id?: string;
  email?: string;
  name?: string;
  username?: string;
}

export interface AuthSession {
  user?: AuthUser;
  token?: string;
}

export async function getServerSession(): Promise<AuthSession | null> {
  try {
    // Try to get token from cookie (set by client after login)
    const cookieStore = await cookies();
    const token = cookieStore.get("auth_token")?.value;

    if (!token) {
      return null;
    }

    // Optional: Verify token is still valid by calling backend
    // For now, just return basic session structure
    // The actual user data should be fetched from client context
    return {
      token,
      user: {
        username: "user", // Placeholder
      },
    };
  } catch (error) {
    console.error("Failed to get server session:", error);
    return null;
  }
}

export async function isAuthenticated(): Promise<boolean> {
  const session = await getServerSession();
  return !!session?.token;
}
