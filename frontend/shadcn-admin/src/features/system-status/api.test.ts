import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchSystemStatus } from './api'

type Snapshot = Awaited<ReturnType<typeof fetchSystemStatus>>

function stubEndpoints(readiness: unknown, readinessStatus = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const isHealth = String(input).endsWith('/health')
      const body = isHealth ? { status: 'healthy' } : readiness
      const status = isHealth ? 200 : readinessStatus

      return Promise.resolve(new Response(JSON.stringify(body), { status }))
    })
  )
}

function expectState(snapshot: Snapshot, id: string, state: string) {
  expect(snapshot.checks.find((check) => check.id === id)?.state).toBe(state)
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('fetchSystemStatus', () => {
  it('maps healthy backend components to operational states', async () => {
    stubEndpoints({
      status: 'ready',
      components: {
        postgres: 'ok',
        redis: 'ok',
        ai_initialized: 'ok',
      },
    })

    const result = await fetchSystemStatus()

    expectState(result, 'postgres', 'operational')
    expectState(result, 'redis', 'operational')
    expectState(result, 'ai', 'operational')
    expect(result.overall).toBe('operational')
  })

  it('preserves component failures returned with HTTP 503', async () => {
    stubEndpoints(
      {
        status: 'not_ready',
        components: {
          postgres: 'ok',
          redis: 'failed',
          ai_initialized: 'ok',
        },
        errors: { redis: 'ConnectionError' },
      },
      503
    )

    const result = await fetchSystemStatus()

    expectState(result, 'postgres', 'operational')
    expectState(result, 'redis', 'outage')
    expect(
      result.checks.find((check) => check.id === 'redis')?.diagnostic
    ).toBe('ConnectionError')
    expectState(result, 'ai', 'operational')
    expect(result.overall).toBe('outage')
  })

  it('keeps missing component data unknown', async () => {
    stubEndpoints({ status: 'ready' })

    const result = await fetchSystemStatus()

    expectState(result, 'postgres', 'unknown')
    expectState(result, 'redis', 'unknown')
    expectState(result, 'ai', 'unknown')
    expect(result.overall).toBe('unknown')
  })
})
