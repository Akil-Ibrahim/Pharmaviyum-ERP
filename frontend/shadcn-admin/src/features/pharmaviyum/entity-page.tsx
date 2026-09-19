import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiFetch } from '@/lib/api-client'

type EntityPageProps = {
  title: string
  description: string
  endpoint?: string
  columns?: string[]
}

type Row = Record<string, unknown>

export function EntityPage({ title, description, endpoint, columns = [] }: EntityPageProps) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(Boolean(endpoint))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!endpoint) return
    apiFetch<Row[]>(endpoint)
      .then(setRows)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load data'))
      .finally(() => setLoading(false))
  }, [endpoint])

  const visibleColumns = columns.length ? columns : rows[0] ? Object.keys(rows[0]).slice(0, 6) : []

  return (
    <div className='space-y-6 p-6'>
      <div><h1 className='text-2xl font-bold tracking-tight'>{title}</h1><p className='text-muted-foreground'>{description}</p></div>
      <Card>
        <CardHeader><CardTitle>{title} records</CardTitle></CardHeader>
        <CardContent>
          {loading && <p className='text-sm text-muted-foreground'>Loading {title.toLowerCase()}...</p>}
          {error && <p className='text-sm text-destructive'>{error}</p>}
          {!loading && !error && rows.length === 0 && <p className='text-sm text-muted-foreground'>No records found.</p>}
          {!loading && !error && rows.length > 0 && (
            <div className='overflow-x-auto'><table className='w-full text-sm'><thead><tr className='border-b text-left text-muted-foreground'>{visibleColumns.map((column) => <th key={column} className='p-3 capitalize'>{column.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={String(row.id ?? index)} className='border-b last:border-0'>{visibleColumns.map((column)=><td key={column} className='p-3'>{formatValue(row[column])}</td>)}</tr>)}</tbody></table></div>
          )}
          {!endpoint && <p className='text-xs text-muted-foreground'>API endpoint is not yet exposed for this entity; the page is ready for the backend integration.</p>}
        </CardContent>
      </Card>
    </div>
  )
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
