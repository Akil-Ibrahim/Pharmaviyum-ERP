import { useAuthStore } from '@/stores/auth-store'

const apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const token = useAuthStore.getState().auth.accessToken
  const headers = new Headers(init.headers)

  headers.set('Accept', 'application/json')
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
  })

  if (response.status === 401) {
    useAuthStore.getState().auth.reset()
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail =
      payload && typeof payload.detail === 'string'
        ? payload.detail
        : `API request failed with status ${response.status}`
    throw new Error(detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
