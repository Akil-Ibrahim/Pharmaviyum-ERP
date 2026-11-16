export type ServiceState = 'operational' | 'degraded' | 'outage' | 'unknown'

export interface ServiceCheck {
  id: 'api' | 'postgres' | 'redis' | 'ai'
  name: string
  state: ServiceState
  description: string
  diagnostic?: string
}

interface HealthPayload {
  status?: string
  service?: string
}

interface ReadinessPayload {
  status?: string
  components?: {
    postgres?: string
    redis?: string
    ai_initialized?: string
  }
  errors?: Record<string, string>
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
    case 'ok':
    case 'healthy':
      return 'operational'
    case 'failed':
    case 'unhealthy':
      return 'outage'
    case 'degraded':
      return 'degraded'
    default:
      return 'unknown'
  }
}

function dependencyDescription(
  component: string | undefined,
  diagnostic: string | undefined,
  endpointReachable: boolean,
  componentName: string
): string {
  if (diagnostic) return diagnostic
  if (component === 'ok') return 'Connection check passed.'
  if (component === 'failed') return 'The readiness check reported a failure.'
  if (!endpointReachable) return 'The readiness endpoint could not be reached.'
  return `No ${componentName} health result was returned.`
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

  // /ready returns HTTP 503 when any critical dependency fails. Its JSON body
  // still contains per-component results, so preserve each individual result.
  const components = readiness?.components
  const errors = readiness?.errors
  const readinessReachable = readiness !== null

  const postgresDiagnostic = errors?.postgres
  const redisDiagnostic = errors?.redis
  const aiDiagnostic = errors?.ai

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
      state: components
        ? dependencyState(components.postgres)
        : readinessReachable
          ? 'unknown'
          : 'outage',
      description: dependencyDescription(
        components?.postgres,
        postgresDiagnostic,
        readinessReachable,
        'PostgreSQL'
      ),
      diagnostic: postgresDiagnostic,
    },
    {
      id: 'redis',
      name: 'Redis',
      state: components
        ? dependencyState(components.redis)
        : readinessReachable
          ? 'unknown'
          : 'outage',
      description: dependencyDescription(
        components?.redis,
        redisDiagnostic,
        readinessReachable,
        'Redis'
      ),
      diagnostic: redisDiagnostic,
    },
    {
      id: 'ai',
      name: 'AI · LangGraph',
      state: components
        ? dependencyState(components.ai_initialized)
        : readinessReachable
          ? 'unknown'
          : 'outage',
      description: dependencyDescription(
        components?.ai_initialized,
        aiDiagnostic,
        readinessReachable,
        'LangGraph initialization'
      ),
      diagnostic: aiDiagnostic,
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
