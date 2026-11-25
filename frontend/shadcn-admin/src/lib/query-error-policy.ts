import { AxiosError } from 'axios'
import { ApiError } from '@/lib/api-error'

export function getHttpStatus(error: unknown): number | undefined {
  if (error instanceof ApiError) return error.status
  if (error instanceof AxiosError) return error.response?.status
  return undefined
}

export function shouldRetryQuery(
  failureCount: number,
  error: unknown,
  isDevelopment: boolean
): boolean {
  if (isDevelopment) return false

  const status = getHttpStatus(error)
  if (status !== undefined && status >= 400 && status < 500) {
    // Timeouts and rate limits may recover; other client errors are not transient.
    return [408, 429].includes(status) && failureCount < 3
  }

  // Retry network failures and server errors at most three times.
  return failureCount < 3
}
