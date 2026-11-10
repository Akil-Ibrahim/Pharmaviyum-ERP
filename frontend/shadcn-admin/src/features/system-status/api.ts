export type ServiceState = 'operational' | 'degraded' | 'outage' | 'unknown'

export interface ServiceCheck {
  id: 'api' | 'postgres' | 'redis' | 'ai'
  name: string
  state: ServiceState
  description: string
  diagnostic?: string
}

interface ReadinessPayload {
  status?: string
  components?: Record<string, string>
  errors?: Record<string, string>
}

interface HealthPayload {
  status?: string
  service?: string
}

export interface SystemStatusSnapshot {
  overall: ServiceState
  checkedAt: string
  checks: ServiceCheck[]
}

const apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

async function getJson<T>(path: string): Promise<{
  responseOk: boolean
  payload: T | null
}> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    const payload = (await response.json().catch(() => null)) as T | null
    return { responseOk: response.ok, payload }
  } catch {
    return { responseOk: false, payload: null }
  }
}

export async function fetchSystemStatus(): Promise<SystemStatusSnapshot> {
  const [healthResult, readinessResult] = await Promise.all([
    getJson<HealthPayload>('/health'),
    getJson<ReadinessPayload>('/ready'),
  ])

  const health = healthResult.payload
  const readiness = readinessResult.payload
  const apiIsHealthy = healthResult.responseOk && health?.status === 'healthy'
  const components = readiness?.components ?? {}
  const errors = readiness?.errors ?? {}

  const checks: ServiceCheck[] = [
    {
      id: 'api',
      name: 'Application · FastAPI Cloud',
      state: apiIsHealthy ? 'operational' : 'outage',
      description: apiIsHealthy
        ? 'The application health endpoint is responding.'
        : 'The application health endpoint did not return a healthy response.',
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      state:
        components.postgres === 'ok'
          ? 'operational'
          : components.postgres === 'failed'
            ? 'outage'
            : 'unknown',
      description:
        components.postgres === 'ok'
          ? 'Database connectivity check passed.'
          : components.postgres === 'failed'
            ? 'The database connectivity check failed.'
            : 'No database health result was returned.',
      diagnostic: errors.postgres,
    },
    {
      id: 'redis',
      name: 'Redis',
      state:
        components.redis === 'ok'
          ? 'operational'
          : components.redis === 'failed'
            ? 'outage'
            : 'unknown',
      description:
        components.redis === 'ok'
          ? 'Redis connectivity check passed.'
          : components.redis === 'failed'
            ? 'The Redis connectivity check failed.'
            : 'No Redis health result was returned.',
      diagnostic: errors.redis,
    },
    {
      id: 'ai',
      name: 'AI · LangGraph',
      state:
        components.ai_initialized === 'ok'
          ? 'operational'
          : components.ai_initialized === 'failed'
            ? 'degraded'
            : 'unknown',
      description:
        components.ai_initialized === 'ok'
          ? 'AI components are initialized.'
          : components.ai_initialized === 'failed'
            ? 'AI components are not initialized.'
            : 'No AI initialization result was returned.',
      diagnostic: errors.ai,
    },
  ]

  const states = checks.map((check) => check.state)
  const overall: ServiceState = states.includes('outage')
    ? 'outage'
    : states.includes('degraded')
      ? 'degraded'
      : states.every((state) => state === 'operational')
        ? 'operational'
        : 'unknown'

  return {
    overall,
    checkedAt: new Date().toISOString(),
    checks,
  }
}
