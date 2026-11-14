export type ServiceState = 'operational' | 'degraded' | 'outage' | 'unknown'

export interface ServiceCheck {
  id: 'api' | 'postgres' | 'redis' | 'ai'
  name: string
  state: ServiceState
  description: string
  diagnostic?: string
}

interface DependencyCheck {
  status?: string
  message?: string
}

interface ReadinessPayload {
  status?: string
  checks?: {
    database?: DependencyCheck
    redis?: DependencyCheck
    [key: string]: DependencyCheck | undefined
  }
}

interface HealthPayload {
  status?: string
  service?: string
  checks?: Record<string, DependencyCheck>
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

function dependencyState(status?: string): ServiceState {
  switch (status) {
    case 'healthy':
      return 'operational'
    case 'degraded':
      return 'degraded'
    case 'unhealthy':
      return 'outage'
    default:
      return 'unknown'
  }
}

export async function fetchSystemStatus(): Promise<SystemStatusSnapshot> {
  const [healthResult, readinessResult] = await Promise.all([
    getJson<HealthPayload>('/health'),
    getJson<ReadinessPayload>('/ready'),
  ])

  const health = healthResult.payload
  const readiness = readinessResult.payload
  const apiState: ServiceState = !healthResult.responseOk
    ? 'outage'
    : health?.status === 'healthy'
      ? 'operational'
      : health?.status === 'degraded'
        ? 'degraded'
        : health?.status === 'unhealthy'
          ? 'outage'
          : 'unknown'

  const database = readiness?.checks?.database
  const redis = readiness?.checks?.redis

  const checks: ServiceCheck[] = [
    {
      id: 'api',
      name: 'Application · FastAPI Cloud',
      state: apiState,
      description:
        apiState === 'operational'
          ? 'The application health endpoint is responding.'
          : apiState === 'degraded'
            ? 'The application is responding with degraded health.'
            : 'The application health endpoint did not return a healthy response.',
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      state: readinessResult.responseOk
        ? dependencyState(database?.status)
        : 'outage',
      description:
        database?.message ??
        (readinessResult.responseOk
          ? 'No database health result was returned.'
          : 'The readiness endpoint could not be reached.'),
      diagnostic: database?.message,
    },
    {
      id: 'redis',
      name: 'Redis',
      state: readinessResult.responseOk
        ? dependencyState(redis?.status)
        : 'outage',
      description:
        redis?.message ??
        (readinessResult.responseOk
          ? 'No Redis health result was returned.'
          : 'The readiness endpoint could not be reached.'),
      diagnostic: redis?.message,
    },
    {
      id: 'ai',
      name: 'AI · LangGraph',
      state: 'unknown',
      description:
        'AI initialization is required at production startup but is not exposed by the current health or readiness response.',
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
