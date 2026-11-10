import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, CircleHelp, RefreshCw, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { fetchSystemStatus, type ServiceCheck, type ServiceState } from './api'

const stateLabels: Record<ServiceState, string> = {
  operational: 'Operational',
  degraded: 'Degraded',
  outage: 'Outage',
  unknown: 'Unknown',
}

const stateClasses: Record<ServiceState, string> = {
  operational: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  degraded: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400',
  outage: 'border-destructive/30 bg-destructive/10 text-destructive',
  unknown: 'border-muted-foreground/20 bg-muted text-muted-foreground',
}

const stateIcons = {
  operational: CheckCircle2,
  degraded: AlertTriangle,
  outage: XCircle,
  unknown: CircleHelp,
}

function formatCheckedAt(value?: string) {
  if (!value) return 'Waiting for first check'

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(value))
}

function ServiceCard({ check }: { check: ServiceCheck }) {
  const StateIcon = stateIcons[check.state]

  return (
    <Card>
      <CardHeader>
        <CardTitle>{check.name}</CardTitle>
        <CardAction>
          <Badge variant='outline' className={stateClasses[check.state]}>
            <StateIcon className='size-3' />
            {stateLabels[check.state]}
          </Badge>
        </CardAction>
        <CardDescription>{check.description}</CardDescription>
      </CardHeader>
      {check.diagnostic && (
        <CardContent>
          <p className='font-mono text-xs text-muted-foreground'>
            Diagnostic: {check.diagnostic}
          </p>
        </CardContent>
      )}
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
        <div>
          <h1 className='text-2xl font-semibold tracking-tight'>
            System Status
          </h1>
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
            className={statusQuery.isFetching ? 'size-4 animate-spin' : 'size-4'}
          />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <OverallIcon className='size-5 text-muted-foreground' />
            Overall system status
          </CardTitle>
          <CardAction>
            <Badge variant='outline' className={stateClasses[overall]}>
              {stateLabels[overall]}
            </Badge>
          </CardAction>
          <CardDescription>{summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className='text-xs text-muted-foreground'>
            Last checked: {formatCheckedAt(statusQuery.data?.checkedAt)}
          </p>
        </CardContent>
      </Card>

      <section className='grid gap-4 sm:grid-cols-2'>
        {statusQuery.data?.checks.map((check) => (
          <ServiceCard key={check.id} check={check} />
        ))}
        {statusQuery.isPending && (
          <p className='text-sm text-muted-foreground'>
            Checking application dependencies…
          </p>
        )}
      </section>

      {statusQuery.error && (
        <p role='alert' className='text-sm text-destructive'>
          {statusQuery.error.message}
        </p>
      )}

      <div className='space-y-2 rounded-lg border p-4'>
        <p className='text-xs text-muted-foreground'>
          The FastAPI Cloud indicator verifies that the hosted application
          responds to its health endpoint. It does not query the provider’s
          private control plane.
        </p>
        <p className='text-xs text-muted-foreground'>
          The AI indicator verifies LangGraph initialization. It does not run a
          live LLM inference request or measure model-provider availability.
        </p>
      </div>
    </main>
  )
}
