import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchSystemStatus } from './api'

describe('fetchSystemStatus', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        if (url.endsWith('/health')) {
          return new Response(JSON.stringify({ status: 'healthy' }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        }
        return new Response(
          JSON.stringify({
            status: 'ready',
            checks: {
              database: { status: 'healthy', message: 'Database connection OK' },
              redis: { status: 'healthy', message: 'Redis connection OK' },
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      })
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('maps the current readiness contract to operational database and Redis states', async () => {
    const snapshot = await fetchSystemStatus()

    expect(snapshot.checks.find((check) => check.id === 'postgres')).toMatchObject({
      state: 'operational',
      description: 'Database connection OK',
    })
    expect(snapshot.checks.find((check) => check.id === 'redis')).toMatchObject({
      state: 'operational',
      description: 'Redis connection OK',
    })
  })

  it('does not claim AI is healthy when the API does not expose an AI readiness check', async () => {
    const snapshot = await fetchSystemStatus()

    expect(snapshot.checks.find((check) => check.id === 'ai')).toMatchObject({
      state: 'unknown',
      description: expect.stringContaining('not exposed'),
    })
    expect(snapshot.overall).toBe('unknown')
  })

  it('reports database and Redis outages from an unsuccessful readiness response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input)
        if (url.endsWith('/health')) {
          return new Response(JSON.stringify({ status: 'healthy' }), {
            status: 200,
          })
        }
        return new Response(
          JSON.stringify({
            status: 'not_ready',
            checks: {
              database: { status: 'unhealthy', message: 'Database connection failed' },
              redis: { status: 'unhealthy', message: 'Redis connection failed' },
            },
          }),
          { status: 503 }
        )
      })
    )

    const snapshot = await fetchSystemStatus()

    expect(snapshot.checks.find((check) => check.id === 'postgres')?.state).toBe(
      'outage'
    )
    expect(snapshot.checks.find((check) => check.id === 'redis')?.state).toBe(
      'outage'
    )
    expect(snapshot.overall).toBe('outage')
  })
})
