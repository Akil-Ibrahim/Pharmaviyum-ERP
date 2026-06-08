/**
 * API Client for backend communication
 * Handles HTTP requests to the backend API with proper error handling and auth
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api/v1';

interface ApiRequestInit extends RequestInit {
  headers?: Record<string, string>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: ApiRequestInit = {}
): Promise<T> {
  const url = new URL(endpoint, `${API_URL}${API_BASE}`);
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add auth token if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url.toString(), {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: response.statusText };
      }
      throw new ApiError(response.status, response.statusText, errorData);
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error(`API request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export const api = {
  get: <T,>(endpoint: string, options?: ApiRequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T,>(endpoint: string, data?: unknown, options?: ApiRequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T,>(endpoint: string, data?: unknown, options?: ApiRequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T,>(endpoint: string, data?: unknown, options?: ApiRequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T,>(endpoint: string, options?: ApiRequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Health check endpoint
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
