/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { RefreshCw, Search } from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

type InventoryRow = {
  id: number
  product_id: number
  pharmacy_id: number
  quantity: number
  reserved_quantity: number
  reorder_level: number
  lot_number: string | null
  expires_at: string | null
}
export const Route = createFileRoute('/_authenticated/inventory')({
  component: InventoryPage,
})
function InventoryPage() {
  const [rows, setRows] = useState<InventoryRow[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState<string | null>(null),
    [query, setQuery] = useState('')
  const load = () => {
    setLoading(true)
    setError(null)
    apiFetch<InventoryRow[]>('/api/v1/inventory')
      .then(setRows)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Unable to load inventory')
      )
      .finally(() => setLoading(false))
  }
  useEffect(() => {
    load()
  }, [])
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return q
      ? rows.filter((r) =>
          [
            r.product_id,
            r.pharmacy_id,
            r.lot_number ?? '',
            r.quantity,
            r.reorder_level,
          ].some((v) => String(v).toLowerCase().includes(q))
        )
      : rows
  }, [rows, query])
  const low = rows.filter(
      (r) => r.quantity - r.reserved_quantity <= r.reorder_level
    ).length,
    out = rows.filter((r) => r.quantity - r.reserved_quantity <= 0).length,
    total = rows.length,
    healthy = total ? Math.round(((total - low) / total) * 100) : 100
  return (
    <div className='space-y-6 p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Inventory</h1>
          <p className='text-muted-foreground'>
            Stock health, reserved quantities, reorder levels, lots, and expiry.
          </p>
        </div>
        <Button variant='outline' size='sm' onClick={load} disabled={loading}>
          <RefreshCw className='mr-2 size-4' />
          Refresh
        </Button>
      </div>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <Metric title='Inventory items' value={total} />
        <Metric title='Low stock' value={low} tone='amber' />
        <Metric title='Out of stock' value={out} tone='red' />
        <Metric title='Inventory health' value={healthy + '%'} tone='green' />
      </div>
      <Card>
        <CardHeader>
          <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
            <CardTitle>Stock ledger</CardTitle>
            <div className='relative w-full sm:max-w-sm'>
              <Search className='absolute top-2.5 left-2.5 size-4 text-muted-foreground' />
              <Input
                className='pl-9'
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Search product, pharmacy, lot...'
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <p className='text-sm text-muted-foreground'>
              Loading inventory...
            </p>
          )}
          {error && <p className='text-sm text-destructive'>{error}</p>}
          {!loading && !error && filtered.length === 0 && (
            <p className='text-sm text-muted-foreground'>
              No inventory records found.
            </p>
          )}
          {!loading && !error && filtered.length > 0 && (
            <div className='overflow-x-auto rounded-md border'>
              <table className='w-full text-sm'>
                <thead>
                  <tr className='border-b bg-muted/40 text-left text-muted-foreground'>
                    <th className='p-3'>Product</th>
                    <th className='p-3'>Pharmacy</th>
                    <th className='p-3'>Lot</th>
                    <th className='p-3 text-right'>Available</th>
                    <th className='p-3 text-right'>Reserved</th>
                    <th className='p-3 text-right'>Reorder</th>
                    <th className='p-3'>Expiry</th>
                    <th className='p-3'>Health</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => {
                    const available = r.quantity - r.reserved_quantity
                    const low = available <= r.reorder_level
                    return (
                      <tr
                        key={r.id}
                        className='border-b last:border-0 hover:bg-muted/30'
                      >
                        <td className='p-3'>{r.product_id}</td>
                        <td className='p-3'>{r.pharmacy_id}</td>
                        <td className='p-3'>{r.lot_number ?? '—'}</td>
                        <td className='p-3 text-right font-medium'>
                          {available}
                        </td>
                        <td className='p-3 text-right'>
                          {r.reserved_quantity}
                        </td>
                        <td className='p-3 text-right'>{r.reorder_level}</td>
                        <td className='p-3'>
                          {r.expires_at
                            ? new Date(r.expires_at).toLocaleDateString()
                            : '—'}
                        </td>
                        <td className='p-3'>
                          <Badge
                            variant='outline'
                            className={
                              available <= 0
                                ? 'bg-red-500/15 text-red-700 dark:text-red-300'
                                : low
                                  ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                                  : 'bg-green-500/15 text-green-700 dark:text-green-300'
                            }
                          >
                            {available <= 0
                              ? 'Out of stock'
                              : low
                                ? 'Low stock'
                                : 'Healthy'}
                          </Badge>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
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
                  : '')
          }
        >
          {value}
        </p>
      </CardContent>
    </Card>
  )
}
