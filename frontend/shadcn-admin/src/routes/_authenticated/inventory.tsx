import { useEffect, useMemo, useState } from 'react'
import {
  type ColumnDef,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { RefreshCw } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { DataTableColumnHeader, DataTablePagination, DataTableToolbar } from '@/components/data-table'
import { PageHeader } from '@/components/page-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiFetch } from '@/lib/api-client'
import { cn } from '@/lib/utils'

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

type InventoryHealth = 'out' | 'low' | 'healthy'

const healthOptions = [
  { label: 'Out of stock', value: 'out' },
  { label: 'Low stock', value: 'low' },
  { label: 'Healthy', value: 'healthy' },
]

function getAvailable(row: InventoryRow) {
  return row.quantity - row.reserved_quantity
}

function getHealth(row: InventoryRow): InventoryHealth {
  const available = getAvailable(row)
  if (available <= 0) return 'out'
  if (available <= row.reorder_level) return 'low'
  return 'healthy'
}

const columns: ColumnDef<InventoryRow>[] = [
  {
    accessorKey: 'product_id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Product ID' />
    ),
    cell: ({ row }) => (
      <span className='font-medium tabular-nums'>{row.original.product_id}</span>
    ),
  },
  {
    accessorKey: 'pharmacy_id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Pharmacy ID' />
    ),
    cell: ({ row }) => row.original.pharmacy_id,
  },
  {
    accessorKey: 'lot_number',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Lot' />
    ),
    cell: ({ row }) => row.original.lot_number || '—',
  },
  {
    id: 'available',
    accessorFn: getAvailable,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Available' />
    ),
    cell: ({ row }) => (
      <span className='font-medium tabular-nums'>
        {getAvailable(row.original)}
      </span>
    ),
    meta: { className: 'text-right', thClassName: 'text-right' },
  },
  {
    accessorKey: 'reserved_quantity',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Reserved' />
    ),
    cell: ({ row }) => row.original.reserved_quantity,
    meta: { className: 'text-right', thClassName: 'text-right' },
  },
  {
    accessorKey: 'reorder_level',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Reorder level' />
    ),
    cell: ({ row }) => row.original.reorder_level,
    meta: { className: 'text-right', thClassName: 'text-right' },
  },
  {
    id: 'expiry',
    accessorFn: (row) =>
      row.expires_at ? new Date(row.expires_at).getTime() : null,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Expiry date' />
    ),
    cell: ({ row }) =>
      row.original.expires_at
        ? new Date(row.original.expires_at).toLocaleDateString('en-US')
        : '—',
  },
  {
    id: 'health',
    accessorFn: getHealth,
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Stock health' />
    ),
    cell: ({ row }) => {
      const health = getHealth(row.original)
      const variants: Record<InventoryHealth, string> = {
        out: 'bg-destructive/10 text-destructive',
        low: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
        healthy: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
      }
      const labels: Record<InventoryHealth, string> = {
        out: 'Out of stock',
        low: 'Low stock',
        healthy: 'Healthy',
      }

      return (
        <Badge variant='outline' className={cn('font-medium', variants[health])}>
          {labels[health]}
        </Badge>
      )
    },
    filterFn: (row, id, value: InventoryHealth[]) =>
      value.includes(row.getValue(id)),
  },
]

export const Route = createFileRoute('/_authenticated/inventory')({
  component: InventoryPage,
})

function InventoryPage() {
  const [rows, setRows] = useState<InventoryRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [columnFilters, setColumnFilters] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')

  const load = () => {
    setLoading(true)
    setError(null)
    apiFetch<InventoryRow[]>('/api/v1/inventory')
      .then(setRows)
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error ? reason.message : 'Unable to load inventory'
        )
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const metrics = useMemo(() => {
    const low = rows.filter((row) => getHealth(row) !== 'healthy').length
    const out = rows.filter((row) => getHealth(row) === 'out').length
    const healthy = rows.length
      ? Math.round(((rows.length - low) / rows.length) * 100)
      : 100

    return { total: rows.length, low, out, healthy }
  }, [rows])

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, columnVisibility, columnFilters, globalFilter },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  })

  return (
    <div className='pharmacy-data-page pharmacy-inventory-page space-y-6 p-6'>
      <PageHeader
        title='Inventory'
        description='Monitor stock levels, reservations, reorder thresholds, lots, and expiry dates.'
        actions={
          <Button variant='outline' size='sm' onClick={load} disabled={loading}>
            <RefreshCw
              className={cn('mr-2 size-4', loading && 'animate-spin')}
            />
            Refresh
          </Button>
        }
      />

      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <Metric title='Inventory items' value={metrics.total} />
        <Metric title='Low stock' value={metrics.low} tone='amber' />
        <Metric title='Out of stock' value={metrics.out} tone='red' />
        <Metric title='Inventory health' value={metrics.healthy + '%'} tone='green' />
      </div>

      <Card>
        <CardHeader className='gap-4'>
          <div className='flex flex-col gap-1'>
            <CardTitle>Stock ledger</CardTitle>
            <p className='text-sm text-muted-foreground'>
              Review available quantities, reservations, reorder levels, and batch expiry.
            </p>
          </div>
          <DataTableToolbar
            table={table}
            searchPlaceholder='Search inventory...'
            filters={[
              {
                columnId: 'health',
                title: 'Stock health',
                options: healthOptions,
              },
            ]}
          />
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className='py-8 text-center text-sm text-muted-foreground'>
              Loading inventory...
            </p>
          ) : error ? (
            <div
              role='alert'
              className='flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm'
            >
              <span>Unable to load inventory: {error}</span>
              <Button variant='outline' size='sm' onClick={load}>
                Retry
              </Button>
            </div>
          ) : (
            <>
              <div className='overflow-hidden rounded-md border'>
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>
                  <TableBody>
                    {table.getRowModel().rows.length ? (
                      table.getRowModel().rows.map((row) => (
                        <TableRow key={row.id}>
                          {row.getVisibleCells().map((cell) => (
                            <TableCell key={cell.id}>
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell
                          colSpan={columns.length}
                          className='h-24 text-center text-muted-foreground'
                        >
                          No inventory records match your filters.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              <DataTablePagination table={table} className='pt-4' />
            </>
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
  tone?: 'amber' | 'red' | 'green'
}) {
  const tones = {
    amber: 'text-amber-600 dark:text-amber-400',
    red: 'text-destructive',
    green: 'text-emerald-600 dark:text-emerald-400',
  }

  return (
    <Card>
      <CardContent className='p-4'>
        <p className='text-xs font-medium text-muted-foreground'>{title}</p>
        <p
          className={cn(
            'mt-2 text-2xl font-semibold tabular-nums',
            tone ? tones[tone] : undefined
          )}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  )
}
