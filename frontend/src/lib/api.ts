/**
 * Centralized API client for FastAPI backend.
 * Handles base URL, auth headers, and JSON parsing.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Helper to attach JWT from localStorage/cookie
const getAuthHeaders = (): Record<string, string> => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
  get: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.statusText}`);
    return res.json();
  },
  post: async <T>(path: string, body: Record<string, unknown>): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`POST ${path} failed: ${res.statusText}`);
    return res.json();
  },
  put: async <T>(path: string, body: Record<string, unknown>): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`PUT ${path} failed: ${res.statusText}`);
    return res.json();
  },
  delete: async <T>(path: string): Promise<T> => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`DELETE ${path} failed: ${res.statusText}`);
    return res.json();
  },
};
