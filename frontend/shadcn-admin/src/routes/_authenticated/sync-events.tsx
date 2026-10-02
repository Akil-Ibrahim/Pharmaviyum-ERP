/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { RefreshCw } from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

type Event = {
  id: number
  integration_id: number
  event_id: string
  entity_type: string
  entity_id: string | null
  direction: string
  status: string
  received_at: string
  processed_at: string | null
}
export const Route = createFileRoute('/_authenticated/sync-events')({
  component: SyncPage,
})
function SyncPage() {
  const [rows, setRows] = useState<Event[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState<string | null>(null)
  const load = () => {
    setLoading(true)
    setError(null)
    apiFetch<Event[]>('/api/v1/sync-events')
      .then(setRows)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Unable to load sync events')
      )
      .finally(() => setLoading(false))
  } // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    load()
  }, [])
  const failed = rows.filter((r) =>
      ['failed', 'error'].includes(r.status.toLowerCase())
    ).length,
    pending = rows.filter((r) =>
      ['received', 'pending', 'processing'].includes(r.status.toLowerCase())
    ).length,
    processed = rows.filter(
      (r) => r.processed_at || r.status.toLowerCase() === 'processed'
    ).length
  return (
    <div className='space-y-6 p-6'>
      <div className='flex justify-between gap-3'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Sync Events</h1>
          <p className='text-muted-foreground'>
            ERP synchronization history and processing health.
          </p>
        </div>
        <Button variant='outline' size='sm' onClick={load} disabled={loading}>
          <RefreshCw className='mr-2 size-4' />
          Refresh
        </Button>
      </div>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <Metric t='Events' v={rows.length} />
        <Metric t='Processed' v={processed} tone='green' />
        <Metric t='Pending' v={pending} tone='amber' />
        <Metric t='Failed' v={failed} tone='red' />
      </div>
      <Card>
        <CardContent className='p-0'>
          {loading && (
            <p className='p-5 text-sm text-muted-foreground'>
              Loading events...
            </p>
          )}
          {error && <p className='p-5 text-sm text-destructive'>{error}</p>}
          {!loading && !error && (
            <div className='overflow-x-auto'>
              <table className='w-full text-sm'>
                <thead>
                  <tr className='border-b bg-muted/40 text-left text-muted-foreground'>
                    <th className='p-3'>Event</th>
                    <th className='p-3'>Entity</th>
                    <th className='p-3'>Direction</th>
                    <th className='p-3'>Status</th>
                    <th className='p-3'>Received</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} className='border-b last:border-0'>
                      <td className='p-3 font-medium'>{r.event_id}</td>
                      <td className='p-3'>
                        {r.entity_type} {r.entity_id ?? ''}
                      </td>
                      <td className='p-3'>{r.direction}</td>
                      <td className='p-3'>
                        <Badge
                          variant='outline'
                          className={
                            failed &&
                            ['failed', 'error'].includes(r.status.toLowerCase())
                              ? 'bg-red-500/15 text-red-700 dark:text-red-300'
                              : pending &&
                                  [
                                    'received',
                                    'pending',
                                    'processing',
                                  ].includes(r.status.toLowerCase())
                                ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                                : 'bg-green-500/15 text-green-700 dark:text-green-300'
                          }
                        >
                          {r.status}
                        </Badge>
                      </td>
                      <td className='p-3 text-muted-foreground'>
                        {new Date(r.received_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
function Metric({ t, v, tone }: { t: string; v: number; tone?: string }) {
  return (
    <Card>
      <CardContent className='p-4'>
        <p className='text-xs text-muted-foreground'>{t}</p>
        <p
          className={
            'mt-2 text-2xl font-semibold ' +
            (tone === 'green'
              ? 'text-emerald-600 dark:text-emerald-400'
              : tone === 'amber'
                ? 'text-amber-600 dark:text-amber-400'
                : tone === 'red'
                  ? 'text-red-600 dark:text-red-400'
                  : '')
          }
        >
          {v}
        </p>
      </CardContent>
    </Card>
  )
}
