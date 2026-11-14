import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchSystemStatus } from './api'

const healthyReadiness = {
  status: 'ready',
  checks: {
    database: { status: 'healthy', message: 'Database OK' },
    redis: { status: 'healthy', message: 'Redis OK' },
  },
}

describe('fetchSystemStatus', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).endsWith('/health')) {
          return new Response(JSON.stringify({ status: 'healthy' }), {
            status: 200,
          })
        }

        return new Response(JSON.stringify(healthyReadiness), {
          status: 200,
        })
      })
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('maps healthy dependencies', async () => {
    const result = await fetchSystemStatus()

    expect(result.checks.find((check) => check.id === 'postgres')?.state).toBe(
      'operational'
    )
    expect(result.checks.find((check) => check.id === 'redis')?.state).toBe(
      'operational'
    )
  })

  it('does not infer AI health from missing API data', async () => {
    const result = await fetchSystemStatus()

    expect(result.checks.find((check) => check.id === 'ai')?.state).toBe(
      'unknown'
    )
    expect(result.overall).toBe('unknown')
  })

  it('reports failed dependencies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).endsWith('/health')) {
          return new Response(JSON.stringify({ status: 'healthy' }), {
            status: 200,
          })
        }

        return new Response(
          JSON.stringify({
            status: 'not_ready',
            checks: {
              database: { status: 'unhealthy' },
              redis: { status: 'unhealthy' },
            },
          }),
          { status: 503 }
        )
      })
    )

    const result = await fetchSystemStatus()

    expect(result.checks.find((check) => check.id === 'postgres')?.state).toBe(
      'outage'
    )
    expect(result.checks.find((check) => check.id === 'redis')?.state).toBe(
      'outage'
    )
    expect(result.overall).toBe('outage')
  })
})
