import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api-error'

const resetAuth = vi.hoisted(() => vi.fn())

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: {
    getState: () => ({
      auth: {
        accessToken: 'test-access-token',
        reset: resetAuth,
      },
    }),
  },
}))

import { apiFetch, apiFetchBlob } from './api-client'

function response(status: number, payload: unknown = null): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: vi.fn().mockResolvedValue(payload),
    blob: vi.fn().mockResolvedValue(new Blob(['image'])),
  } as unknown as Response
}

describe('apiFetch HTTP error contract', () => {
  beforeEach(() => {
    resetAuth.mockClear()
    vi.unstubAllGlobals()
  })

  it('throws ApiError with the HTTP status and server detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        response(422, { detail: 'Cash received is less than the sale total' })
      )
    )

    await expect(apiFetch('/api/v1/pos/checkout')).rejects.toMatchObject({
      name: 'ApiError',
      status: 422,
      message: 'Cash received is less than the sale total',
    })
  })

  it('resets the local session and preserves 401 as a typed error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(response(401, { detail: 'Not authenticated' }))
    )

    await expect(apiFetch('/api/v1/users/me')).rejects.toBeInstanceOf(ApiError)
    await expect(apiFetch('/api/v1/users/me')).rejects.toMatchObject({
      status: 401,
    })
    expect(resetAuth).toHaveBeenCalledTimes(2)
  })

  it('returns undefined for a successful 204 response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(204)))

    await expect(apiFetch<void>('/api/v1/example')).resolves.toBeUndefined()
  })

  it('returns null for a missing optional blob', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(404)))

    await expect(apiFetchBlob('/users/me/avatar')).resolves.toBeNull()
  })
})
