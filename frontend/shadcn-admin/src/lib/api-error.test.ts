import { describe, expect, it } from 'vitest'
import { ApiError } from './api-error'

describe('ApiError', () => {
  it('preserves HTTP status, server payload and readable message', () => {
    const payload = { detail: 'Pharmacy access denied' }
    const error = new ApiError(403, 'Pharmacy access denied', payload)

    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe('ApiError')
    expect(error.status).toBe(403)
    expect(error.message).toBe('Pharmacy access denied')
    expect(error.payload).toBe(payload)
  })
})
