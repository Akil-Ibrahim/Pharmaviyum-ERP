import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { ApiError } from './api-error'
import { getHttpStatus, shouldRetryQuery } from './query-error-policy'

describe('query HTTP error policy', () => {
  it.each([401, 403, 404, 422])(
    'does not retry non-transient HTTP %i errors',
    (status) => {
      expect(
        shouldRetryQuery(
          0,
          new ApiError(status, 'Request rejected', null),
          false
        )
      ).toBe(false)
    }
  )

  it.each([408, 429])(
    'retries transient HTTP %i errors within the retry limit',
    (status) => {
      const error = new ApiError(status, 'Transient response', null)

      expect(shouldRetryQuery(0, error, false)).toBe(true)
      expect(shouldRetryQuery(2, error, false)).toBe(true)
      expect(shouldRetryQuery(3, error, false)).toBe(false)
    }
  )

  it('retries server and network errors at most three times', () => {
    expect(
      shouldRetryQuery(0, new ApiError(503, 'Unavailable', null), false)
    ).toBe(true)
    expect(shouldRetryQuery(2, new Error('Network failure'), false)).toBe(true)
    expect(shouldRetryQuery(3, new Error('Network failure'), false)).toBe(false)
  })

  it('applies the same status policy to Axios errors', () => {
    const error = new AxiosError('Forbidden')
    error.response = { status: 403 } as AxiosError['response']

    expect(getHttpStatus(error)).toBe(403)
    expect(shouldRetryQuery(0, error, false)).toBe(false)
  })

  it('disables automatic retries in development', () => {
    expect(
      shouldRetryQuery(0, new ApiError(503, 'Unavailable', null), true)
    ).toBe(false)
  })
})
