import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchSystemStatus } from './api'

const healthyReadiness = {
  status: 'ready',
  components: {
    postgres: 'ok',
    redis: 'ok',
    ai_initialized: 'ok',
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

  it('maps ready components', async () => {
      const result = await fetchSystemStatus()

      expect(
        result.checks.find((check) => check.id === 'postgres')?.state
      ).toBe('operational')
      expect(
        result.checks.find((check) => check.id === 'redis')?.state
      ).toBe('operational')
      expect(
        result.checks.find((check) => check.id === 'ai')?.state
      ).toBe('operational')
      expect(result.overall).toBe('operational')
  })

  it('preserves component results on HTTP 503', async () => {
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
              components: {
                postgres: 'ok',
                redis: 'failed',
                ai_initialized: 'ok',
              },
              errors: { redis: 'ConnectionError' },
            }),
            { status: 503 }
          )
        })
      )

      const result = await fetchSystemStatus()

      expect(
        result.checks.find((check) => check.id === 'postgres')?.state
      ).toBe('operational')
      expect(
        result.checks.find((check) => check.id === 'redis')?.state
      ).toBe('outage')
      expect(
        result.checks.find((check) => check.id === 'redis')?.diagnostic
      ).toBe('ConnectionError')
      expect(
        result.checks.find((check) => check.id === 'ai')?.state
      ).toBe('operational')
      expect(result.overall).toBe('outage')
    }
  )

  it('keeps missing component data unknown', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn(async (input: RequestInfo | URL) => {
          if (String(input).endsWith('/health')) {
            return new Response(JSON.stringify({ status: 'healthy' }), {
              status: 200,
            })
          }

          return new Response(JSON.stringify({ status: 'ready' }), {
            status: 200,
          })
        })
      )

      const result = await fetchSystemStatus()

      expect(
        result.checks.find((check) => check.id === 'postgres')?.state
      ).toBe('unknown')
      expect(
        result.checks.find((check) => check.id === 'redis')?.state
      ).toBe('unknown')
      expect(
        result.checks.find((check) => check.id === 'ai')?.state
      ).toBe('unknown')
      expect(result.overall).toBe('unknown')
    }
  )
})
