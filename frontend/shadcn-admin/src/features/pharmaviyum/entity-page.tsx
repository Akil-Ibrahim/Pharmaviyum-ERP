import { useCallback, useEffect, useMemo, useState } from 'react'
import { Search, RefreshCw } from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

type EntityPageProps = {
  title: string
  description: string
  endpoint?: string
  columns?: string[]
  status?: string
}

type Row = Record<string, unknown>

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-500/15 text-green-700 dark:text-green-300',
  completed: 'bg-green-500/15 text-green-700 dark:text-green-300',
  success: 'bg-green-500/15 text-green-700 dark:text-green-300',
  pending: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
  processing: 'bg-blue-500/15 text-blue-700 dark:text-blue-300',
  cancelled: 'bg-red-500/15 text-red-700 dark:text-red-300',
  failed: 'bg-red-500/15 text-red-700 dark:text-red-300',
  inactive: 'bg-muted text-muted-foreground',
}

export function EntityPage({
  title,
  description,
  endpoint,
  columns = [],
  status,
}: EntityPageProps) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(Boolean(endpoint))
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  const load = useCallback(() => {
    if (!endpoint) return
    setLoading(true)
    setError(null)
    apiFetch<Row[]>(endpoint)
      .then(setRows)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'Unable to load data')
      )
      .finally(() => setLoading(false))
  }, [endpoint])

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const visibleColumns = columns.length
    ? columns
    : rows[0]
      ? Object.keys(rows[0]).slice(0, 6)
      : []
  const filteredRows = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return rows
    return rows.filter((row) =>
      Object.values(row).some((value) =>
        formatValue(value).toLowerCase().includes(normalized)
      )
    )
  }, [rows, query])

  const statusCounts = useMemo(() => {
    const result: Record<string, number> = {}
    rows.forEach((row) => {
      const value = row.status ?? row.is_active
      if (value !== undefined && value !== null) {
        const key =
          typeof value === 'boolean'
            ? value
              ? 'active'
              : 'inactive'
            : String(value).toLowerCase()
        result[key] = (result[key] ?? 0) + 1
      }
    })
    return result
  }, [rows])

  return (
    <div className='space-y-6 p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>{title}</h1>
          <p className='text-muted-foreground'>{description}</p>
        </div>
        {endpoint && (
          <Button variant='outline' size='sm' onClick={load} disabled={loading}>
            <RefreshCw className='mr-2 size-4' />
            Refresh
          </Button>
        )}
      </div>

      {status && <Badge variant='secondary'>{status}</Badge>}

      {rows.length > 0 && (
        <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-4'>
          <MetricCard label='Total' value={rows.length} />
          {Object.entries(statusCounts)
            .slice(0, 3)
            .map(([key, value]) => (
              <MetricCard key={key} label={formatLabel(key)} value={value} />
            ))}
        </div>
      )}

      <Card>
        <CardHeader className='gap-4'>
          <div className='flex items-center justify-between gap-3'>
            <CardTitle>{title} records</CardTitle>
            {rows.length > 0 && (
              <span className='text-xs text-muted-foreground'>
                {filteredRows.length} of {rows.length}
              </span>
            )}
          </div>
          {rows.length > 0 && (
            <div className='relative max-w-sm'>
              <Search className='absolute top-2.5 left-2.5 size-4 text-muted-foreground' />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={`Search ${title.toLowerCase()}...`}
                className='pl-9'
              />
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading && (
            <p className='text-sm text-muted-foreground'>
              Loading {title.toLowerCase()}...
            </p>
          )}
          {error && <p className='text-sm text-destructive'>{error}</p>}
          {!loading && !error && rows.length === 0 && (
            <p className='text-sm text-muted-foreground'>No records found.</p>
          )}
          {!loading && !error && filteredRows.length > 0 && (
            <div className='overflow-x-auto rounded-md border'>
              <table className='w-full text-sm'>
                <thead>
                  <tr className='border-b bg-muted/40 text-left text-muted-foreground'>
                    {visibleColumns.map((column) => (
                      <th
                        key={column}
                        className='p-3 font-medium whitespace-nowrap'
                      >
                        {formatLabel(column)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row, index) => (
                    <tr
                      key={String(row.id ?? index)}
                      className='border-b last:border-0 hover:bg-muted/30'
                    >
                      {visibleColumns.map((column) => (
                        <td
                          key={column}
                          className='max-w-[280px] p-3 align-top'
                        >
                          {formatCell(row[column], column)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!loading &&
            !error &&
            rows.length > 0 &&
            filteredRows.length === 0 && (
              <p className='text-sm text-muted-foreground'>
                No records match your search.
              </p>
            )}
          {!endpoint && (
            <p className='text-xs text-muted-foreground'>
              API endpoint is not yet exposed for this entity; the page is ready
              for the backend integration.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className='p-4'>
        <p className='text-xs font-medium text-muted-foreground'>{label}</p>
        <p className='mt-1 text-2xl font-semibold tracking-tight'>
          {value.toLocaleString()}
        </p>
      </CardContent>
    </Card>
  )
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatCell(value: unknown, column: string) {
  if (value === null || value === undefined || value === '') return '—'
  if (column === 'status' || column === 'is_active') {
    const key =
      typeof value === 'boolean'
        ? value
          ? 'active'
          : 'inactive'
        : String(value).toLowerCase()
    return (
      <Badge variant='outline' className={STATUS_COLORS[key] ?? ''}>
        {formatLabel(key)}
      </Badge>
    )
  }
  return formatValue(value)
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
