import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type Batch = {
  id: number
  product_id: number
  batch_number: string
  expiry_date: string
  received_quantity: number
  available_quantity: number
  barcode: string | null
  days_to_expiry: number
  expiry_status: 'red' | 'yellow' | 'green'
  expiry_alert: 'expired' | '3_months' | '9_months' | '12_months' | 'none'
}

type AlertFilter = 'all' | '12_months' | '9_months' | '3_months' | 'expired'

export const Route = createFileRoute('/_authenticated/batches')({
  component: BatchesPage,
})

function BatchesPage() {
  const [rows, setRows] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [alertFilter, setAlertFilter] = useState<AlertFilter>('all')

  const load = () => {
    setLoading(true)
    setError(null)
    apiFetch<Batch[]>('/api/v1/batches')
      .then(setRows)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Unable to load batches')
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      const matchesAlert =
        alertFilter === 'all' || row.expiry_alert === alertFilter
      const matchesQuery =
        !q ||
        [row.product_id, row.batch_number, row.barcode ?? ''].some((value) =>
          String(value).toLowerCase().includes(q)
        )
      return matchesAlert && matchesQuery
    })
  }, [rows, query, alertFilter])

  const critical = rows.filter((row) => row.expiry_status === 'red').length
  const warning = rows.filter((row) => row.expiry_status === 'yellow').length
  const good = rows.filter((row) => row.expiry_status === 'green').length
  const alert12 = rows.filter((row) => row.expiry_alert === '12_months').length
  const alert9 = rows.filter((row) => row.expiry_alert === '9_months').length
  const alert3 = rows.filter((row) => row.expiry_alert === '3_months').length

  return (
    <div className='space-y-6 p-6'>
      <div className='flex justify-between gap-3'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Batches</h1>
          <p className='text-muted-foreground'>
            Medication batch traceability, expiry risk, FEFO support, and expiry
            alerts.
          </p>
        </div>
        <Button variant='outline' size='sm' onClick={load} disabled={loading}>
          <RefreshCw className='mr-2 size-4' />
          Refresh
        </Button>
      </div>

      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-7'>
        <Metric title='Batches' value={rows.length} />
        <Metric title='🔴 Critical ≤30d' value={critical} tone='red' />
        <Metric title='🟡 Warning 31–90d' value={warning} tone='amber' />
        <Metric title='🟢 Good >90d' value={good} tone='green' />
        <Metric title='12-month alert' value={alert12} tone='blue' />
        <Metric title='9-month alert' value={alert9} tone='blue' />
        <Metric title='3-month alert' value={alert3} tone='amber' />
      </div>

      <Card>
        <CardHeader>
          <div className='flex flex-col gap-3'>
            <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
              <CardTitle>Batch ledger</CardTitle>
              <div className='relative w-full sm:max-w-sm'>
                <Search className='absolute left-2.5 top-2.5 size-4 text-muted-foreground' />
                <Input
                  className='pl-9'
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder='Search batches...'
                />
              </div>
            </div>
            <div className='flex flex-wrap gap-2'>
              <AlertButton
                active={alertFilter === 'all'}
                onClick={() => setAlertFilter('all')}
              >
                All
              </AlertButton>
              <AlertButton
                active={alertFilter === '12_months'}
                onClick={() => setAlertFilter('12_months')}
              >
                12 months
              </AlertButton>
              <AlertButton
                active={alertFilter === '9_months'}
                onClick={() => setAlertFilter('9_months')}
              >
                9 months
              </AlertButton>
              <AlertButton
                active={alertFilter === '3_months'}
                onClick={() => setAlertFilter('3_months')}
              >
                3 months
              </AlertButton>
              <AlertButton
                active={alertFilter === 'expired'}
                onClick={() => setAlertFilter('expired')}
              >
                Expired
              </AlertButton>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {loading && (
            <p className='text-sm text-muted-foreground'>Loading batches...</p>
          )}
          {error && <p className='text-sm text-destructive'>{error}</p>}
          {!loading && !error && filtered.length > 0 && (
            <div className='overflow-x-auto rounded-md border'>
              <table className='w-full text-sm'>
                <thead>
                  <tr className='border-b bg-muted/40 text-left text-muted-foreground'>
                    <th className='p-3'>Batch</th>
                    <th className='p-3'>Product</th>
                    <th className='p-3'>Expiry</th>
                    <th className='p-3 text-right'>Available</th>
                    <th className='p-3'>Barcode</th>
                    <th className='p-3'>Days left</th>
                    <th className='p-3'>Planning alert</th>
                    <th className='p-3'>Operational status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((row) => {
                    const status = row.expiry_status
                    const label =
                      row.expiry_alert === 'expired'
                        ? 'Expired'
                        : status === 'red'
                          ? 'Critical'
                          : status === 'yellow'
                            ? 'Warning'
                            : 'Good'
                    const alertLabel =
                      row.expiry_alert === 'expired'
                        ? 'Expired'
                        : row.expiry_alert === '3_months'
                          ? '3 months'
                          : row.expiry_alert === '9_months'
                            ? '9 months'
                            : row.expiry_alert === '12_months'
                              ? '12 months'
                              : '—'

                    return (
                      <tr
                        key={row.id}
                        className='border-b last:border-0 hover:bg-muted/30'
                      >
                        <td className='p-3 font-medium'>{row.batch_number}</td>
                        <td className='p-3'>{row.product_id}</td>
                        <td className='p-3'>
                          {new Date(row.expiry_date).toLocaleDateString()}
                        </td>
                        <td className='p-3 text-right'>
                          {row.available_quantity}
                        </td>
                        <td className='p-3'>{row.barcode ?? '—'}</td>
                        <td className='p-3'>{row.days_to_expiry}</td>
                        <td className='p-3'>
                          <Badge variant='outline'>{alertLabel}</Badge>
                        </td>
                        <td className='p-3'>
                          <Badge
                            variant='outline'
                            className={
                              status === 'red'
                                ? 'bg-red-500/15 text-red-700 dark:text-red-300'
                                : status === 'yellow'
                                  ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                                  : 'bg-green-500/15 text-green-700 dark:text-green-300'
                            }
                          >
                            {label}
                          </Badge>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <p className='text-sm text-muted-foreground'>No batches found.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function AlertButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: string
}) {
  return (
    <Button variant={active ? 'default' : 'outline'} size='sm' onClick={onClick}>
      {children}
    </Button>
  )
}

function Metric({
  title,
  value,
  tone,
}: {
  title: string
  value: string | number
  tone?: string
}) {
  return (
    <Card>
      <CardContent className='p-4'>
        <p className='text-xs font-medium text-muted-foreground'>{title}</p>
        <p
          className={
            'mt-2 text-2xl font-semibold ' +
            (tone === 'green'
              ? 'text-emerald-600 dark:text-emerald-400'
              : tone === 'amber'
                ? 'text-amber-600 dark:text-amber-400'
                : tone === 'red'
                  ? 'text-red-600 dark:text-red-400'
                  : tone === 'blue'
                    ? 'text-blue-600 dark:text-blue-400'
                    : '')
          }
        >
          {value}
        </p>
      </CardContent>
    </Card>
  )
}
