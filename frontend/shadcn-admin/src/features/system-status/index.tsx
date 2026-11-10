import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  CircleHelp,
  Cloud,
  Database,
  RefreshCw,
  Server,
  XCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  fetchSystemStatus,
  type ServiceCheck,
  type ServiceState,
} from './api'

const stateLabels: Record<ServiceState, string> = {
  operational: 'Operational',
  degraded: 'Degraded',
  outage: 'Outage',
  unknown: 'Unknown',
}

const stateClasses: Record<ServiceState, string> = {
  operational:
    'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  degraded:
    'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400',
  outage: 'border-destructive/30 bg-destructive/10 text-destructive',
  unknown: 'border-muted-foreground/20 bg-muted text-muted-foreground',
}

const stateIcons = {
  operational: CheckCircle2,
  degraded: AlertTriangle,
  outage: XCircle,
  unknown: CircleHelp,
}

const serviceIcons = {
  api: Cloud,
  postgres: Database,
  redis: Server,
  ai: Bot,
}

function formatCheckedAt(value?: string) {
  if (!value) return 'Waiting for first check'

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(value))
}

function ServiceCard({ check }: { check: ServiceCheck }) {
  const Icon = serviceIcons[check.id]
  const StateIcon = stateIcons[check.state]

  return (
    <Card>
      <CardHeader className='grid-cols-[1fr_auto] items-start'>
        <div className='flex items-center gap-3'>
          <span className='flex size-10 items-center justify-center rounded-lg bg-muted'>
            <Icon className='size-5 text-muted-foreground' />
          </span>
          <div className='space-y-1'>
            <CardTitle className='text-base'>{check.name}</CardTitle>
            <CardDescription>Live health check</CardDescription>
          </div>
        </div>
        <Badge variant='outline' className={stateClasses[check.state]}>
          <StateIcon className='size-3' />
          {stateLabels[check.state]}
        </Badge>
      </CardHeader>
      <CardContent className='space-y-2'>
        <p className='text-sm text-muted-foreground'>{check.description}</p>
        {check.diagnostic && (
          <p className='rounded-md bg-muted px-3 py-2 font-mono text-xs text-muted-foreground'>
            Diagnostic: {check.diagnostic}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function SystemStatusPage() {
  const statusQuery = useQuery({
    queryKey: ['system-status'],
    queryFn: fetchSystemStatus,
    refetchInterval: 30_000,
    staleTime: 10_000,
    retry: 1,
  })

  const overall = statusQuery.data?.overall ?? 'unknown'
  const OverallIcon = stateIcons[overall]
  const summary = statusQuery.isPending
    ? 'Running the first health check…'
    : statusQuery.error
      ? 'Unable to retrieve system health information.'
      : overall === 'operational'
        ? 'All monitored components are operational.'
        : 'One or more components need attention.'

  return (
    <main className='space-y-6 p-4 md:p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
        <div className='space-y-1'>
          <div className='flex items-center gap-2'>
            <Activity className='size-5 text-muted-foreground' />
            <h1 className='text-2xl font-semibold tracking-tight'>
              System Status
            </h1>
          </div>
          <p className='text-sm text-muted-foreground'>
            Live health checks for the Pharmaviyum application and its core
            dependencies.
          </p>
        </div>
        <Button
          variant='outline'
          size='sm'
          onClick={() => void statusQuery.refetch()}
          disabled={statusQuery.isFetching}
        >
          <RefreshCw
            className={
              statusQuery.isFetching ? 'size-4 animate-spin' : 'size-4'
            }
          />
          Refresh
        </Button>
      </div>

      <Card>
        <CardContent className='flex flex-col gap-3 py-5 sm:flex-row sm:items-center sm:justify-between'>
          <div className='flex items-center gap-3'>
            <span className='flex size-11 items-center justify-center rounded-full bg-muted'>
              <OverallIcon className='size-5 text-muted-foreground' />
            </span>
            <div className='space-y-1'>
              <p className='font-medium'>Overall system status</p>
              <p className='text-sm text-muted-foreground'>{summary}</p>
            </div>
          </div>
          <div className='flex flex-col items-start gap-1 sm:items-end'>
            <Badge variant='outline' className={stateClasses[overall]}>
              {stateLabels[overall]}
            </Badge>
            <span className='text-xs text-muted-foreground'>
              Last checked: {formatCheckedAt(statusQuery.data?.checkedAt)}
            </span>
          </div>
        </CardContent>
      </Card>

      <section className='grid gap-4 sm:grid-cols-2'>
        {statusQuery.data?.checks.map((check) => (
          <ServiceCard key={check.id} check={check} />
        ))}
        {statusQuery.isPending &&
          ['api', 'postgres', 'redis', 'ai'].map((item) => (
            <Card key={item}>
              <CardContent className='flex h-28 items-center gap-3'>
                <span className='size-10 animate-pulse rounded-lg bg-muted' />
                <span className='h-4 w-32 animate-pulse rounded bg-muted' />
              </CardContent>
            </Card>
          ))}
      </section>

      <div className='space-y-2 rounded-lg border bg-muted/30 p-4 text-xs text-muted-foreground'>
        <p>
          Checks run automatically every 30 seconds. The API status confirms
          application availability through FastAPI Cloud; it does not query the
          hosting provider’s private control plane.
        </p>
        <p>
          The AI indicator verifies LangGraph component initialization. It does
          not execute a live LLM inference request or measure model-provider
          availability.
        </p>
      </div>
    </main>
  )
}
