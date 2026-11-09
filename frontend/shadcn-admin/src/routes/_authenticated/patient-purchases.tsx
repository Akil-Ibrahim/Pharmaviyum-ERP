import { useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  type ColumnDef,
  type ColumnFiltersState,
  type PaginationState,
  type SortingState,
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
import { apiFetch } from '@/lib/api-client'
import { cn } from '@/lib/utils'
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
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DataTableColumnHeader,
  DataTablePagination,
  DataTableToolbar,
} from '@/components/data-table'
import { PageHeader } from '@/components/page-header'

type PatientPurchase = {
  id: number
  patient_id: number
  product_id: number | null
  product_name: string | null
  batch_id: number | null
  batch_number: string | null
  receipt_number: string
  category: string
  quantity: number
  dispensed_packs: number
  dispensed_blisters: number
  dispensed_units: number
  unit_price: number
  total_amount: number
  prescription_required: boolean
  purchased_at: string
  expiry_date: string | null
}

const money = (value: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'UAH',
    maximumFractionDigits: 2,
  }).format(value)

const formatDateTime = (value: string | null) => {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
}

// The API returns expiry_date as a calendar date, not a timestamp.
// Parse its components directly so the displayed day cannot shift by timezone.
const formatCalendarDate = (value: string | null) => {
  if (!value) return '—'
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  if (!match) return '—'
  const [, year, month, day] = match
  const date = new Date(Number(year), Number(month) - 1, Number(day))
  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
}

const columns: ColumnDef<PatientPurchase>[] = [
  {
    accessorKey: 'receipt_number',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Receipt' />
    ),
    cell: ({ row }) => (
      <span className='font-semibold text-primary'>
        {row.original.receipt_number}
      </span>
    ),
  },
  {
    id: 'product',
    accessorFn: (row) => row.product_name ?? 'Unlinked purchase',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Product' />
    ),
    cell: ({ row }) => (
      <div className='min-w-36'>
        <p className='max-w-56 truncate font-medium'>
          {row.original.product_name ?? 'Unlinked purchase'}
        </p>
        {row.original.product_id !== null && (
          <p className='text-xs text-muted-foreground'>
            Product #{row.original.product_id}
          </p>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'patient_id',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Patient' />
    ),
    cell: ({ row }) => (
      <span className='tabular-nums'>#{row.original.patient_id}</span>
    ),
  },
  {
    accessorKey: 'category',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Category' />
    ),
    cell: ({ row }) => (
      <Badge variant='outline' className='font-medium'>
        {row.original.category}
      </Badge>
    ),
    filterFn: (row, id, value: string[]) => value.includes(row.getValue(id)),
  },
  {
    accessorKey: 'quantity',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Qty' />
    ),
    cell: ({ row }) => (
      <span className='font-medium tabular-nums'>{row.original.quantity}</span>
    ),
    meta: { className: 'text-right', thClassName: 'text-right' },
  },
  {
    accessorKey: 'total_amount',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Total' />
    ),
    cell: ({ row }) => (
      <span className='font-semibold tabular-nums'>
        {money(row.original.total_amount)}
      </span>
    ),
    meta: { className: 'text-right', thClassName: 'text-right' },
  },
  {
    accessorFn: (row) => new Date(row.purchased_at).getTime(),
    id: 'purchased_at',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Purchased' />
    ),
    cell: ({ row }) => (
      <span className='whitespace-nowrap text-muted-foreground'>
        {formatDateTime(row.original.purchased_at)}
      </span>
    ),
  },
  {
    accessorKey: 'prescription_required',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Prescription' />
    ),
    cell: ({ row }) =>
      row.original.prescription_required ? (
        <Badge variant='secondary'>Required</Badge>
      ) : (
        <span className='text-sm text-muted-foreground'>Not required</span>
      ),
    filterFn: (row, id, value: string[]) =>
      value.includes(row.getValue(id) ? 'required' : 'not_required'),
  },
]

export const Route = createFileRoute('/_authenticated/patient-purchases')({
  component: PatientPurchasesPage,
})

function PatientPurchasesPage() {
  const [purchases, setPurchases] = useState<PatientPurchase[]>([])
  const [selectedPurchase, setSelectedPurchase] =
    useState<PatientPurchase | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'purchased_at', desc: true },
  ])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  })

  const load = () => {
    setLoading(true)
    setError(null)
    apiFetch<PatientPurchase[]>('/api/v1/patient-purchases/?limit=50')
      .then(setPurchases)
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : 'Unable to load purchase records'
        )
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const categoryOptions = useMemo(
    () =>
      Array.from(new Set(purchases.map((purchase) => purchase.category)))
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b))
        .map((category) => ({ label: category, value: category })),
    [purchases]
  )

  const metrics = useMemo(
    () => ({
      records: purchases.length,
      packs: purchases.reduce(
        (total, purchase) => total + purchase.dispensed_packs,
        0
      ),
      value: purchases.reduce(
        (total, purchase) => total + purchase.total_amount,
        0
      ),
    }),
    [purchases]
  )

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: purchases,
    columns,
    state: { sorting, columnFilters, globalFilter, pagination },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  })

  return (
    <div className='pharmacy-data-page space-y-6 p-6'>
      <PageHeader
        title='Patient Purchases'
        description='Purchase ledger, receipt references, dispensed quantities, and recorded value.'
        actions={
          <Button variant='outline' size='sm' onClick={load} disabled={loading}>
            <RefreshCw
              className={cn('mr-2 size-4', loading && 'animate-spin')}
            />
            Refresh
          </Button>
        }
      />

      <section className='grid gap-4 sm:grid-cols-3'>
        <MetricCard
          label='Records loaded'
          value={metrics.records.toLocaleString('en-US')}
          note='Latest API result'
        />
        <MetricCard
          label='Packs dispensed'
          value={metrics.packs.toLocaleString('en-US')}
          note='Within loaded records'
        />
        <MetricCard
          label='Recorded purchase value'
          value={money(metrics.value)}
          note='Within loaded records'
        />
      </section>

      <Card className='gap-0 py-0'>
        <CardHeader className='gap-4 border-b px-5 py-5'>
          <div className='flex flex-col gap-1'>
            <CardTitle>Purchase ledger</CardTitle>
            <CardDescription>
              Showing the latest 50 records returned by the purchase API. Select
              a row to inspect its receipt and batch details.
            </CardDescription>
          </div>
          <DataTableToolbar
            table={table}
            searchPlaceholder='Search receipt, product, patient...'
            filters={[
              {
                columnId: 'category',
                title: 'Category',
                options: categoryOptions,
              },
              {
                columnId: 'prescription_required',
                title: 'Prescription',
                options: [
                  { label: 'Required', value: 'required' },
                  { label: 'Not required', value: 'not_required' },
                ],
              },
            ]}
          />
        </CardHeader>
        <CardContent className='p-0'>
          {loading ? (
            <div className='space-y-3 p-5'>
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className='h-10 w-full' />
              ))}
            </div>
          ) : error ? (
            <div
              role='alert'
              className='m-5 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm'
            >
              <span>Unable to load purchase records: {error}</span>
              <Button variant='outline' size='sm' onClick={load}>
                Retry
              </Button>
            </div>
          ) : (
            <>
              <div className='overflow-x-auto'>
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead
                            key={header.id}
                            className={cn(
                              ['quantity', 'total_amount'].includes(
                                header.column.id
                              ) && 'text-right'
                            )}
                          >
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
                    {table.getRowModel().rows.length > 0 ? (
                      table.getRowModel().rows.map((row) => (
                        <TableRow
                          key={row.id}
                          tabIndex={0}
                          className='cursor-pointer'
                          aria-label={`Open receipt ${row.original.receipt_number}`}
                          onClick={() => setSelectedPurchase(row.original)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault()
                              setSelectedPurchase(row.original)
                            }
                          }}
                        >
                          {row.getVisibleCells().map((cell) => (
                            <TableCell
                              key={cell.id}
                              className={cn(
                                ['quantity', 'total_amount'].includes(
                                  cell.column.id
                                ) && 'text-right'
                              )}
                            >
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
                          className='h-28 text-center text-muted-foreground'
                        >
                          No purchase records match the current filters.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              <div className='border-t p-4'>
                <DataTablePagination table={table} />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Sheet
        open={Boolean(selectedPurchase)}
        onOpenChange={(open) => {
          if (!open) setSelectedPurchase(null)
        }}
      >
        <SheetContent className='w-full overflow-y-auto sm:max-w-lg'>
          {selectedPurchase && (
            <>
              <SheetHeader className='border-b pb-5'>
                <p className='text-xs font-medium tracking-wide text-muted-foreground uppercase'>
                  Purchase receipt
                </p>
                <SheetTitle className='text-xl'>
                  {selectedPurchase.receipt_number}
                </SheetTitle>
                <SheetDescription>
                  Recorded {formatDateTime(selectedPurchase.purchased_at)}
                </SheetDescription>
                <div className='pt-2'>
                  <Badge variant='outline'>{selectedPurchase.category}</Badge>
                </div>
              </SheetHeader>

              <div className='space-y-6 px-4 pb-6'>
                <section className='rounded-xl border bg-muted/20 p-4'>
                  <p className='text-xs font-medium text-muted-foreground'>
                    Recorded total
                  </p>
                  <p className='mt-1 text-3xl font-semibold tracking-tight tabular-nums'>
                    {money(selectedPurchase.total_amount)}
                  </p>
                  <p className='mt-1 text-xs text-muted-foreground'>
                    {money(selectedPurchase.unit_price)} per recorded unit
                  </p>
                </section>

                <DetailSection title='Purchase details'>
                  <Detail
                    label='Patient'
                    value={`#${selectedPurchase.patient_id}`}
                  />
                  <Detail
                    label='Product'
                    value={
                      selectedPurchase.product_name ??
                      'No linked product record'
                    }
                  />
                  <Detail
                    label='Product ID'
                    value={selectedPurchase.product_id ?? '—'}
                  />
                  <Detail label='Quantity' value={selectedPurchase.quantity} />
                  <Detail
                    label='Prescription'
                    value={
                      selectedPurchase.prescription_required
                        ? 'Required'
                        : 'Not required'
                    }
                  />
                </DetailSection>

                <DetailSection title='Dispensing and batch'>
                  <Detail
                    label='Packs'
                    value={selectedPurchase.dispensed_packs}
                  />
                  <Detail
                    label='Blisters'
                    value={selectedPurchase.dispensed_blisters}
                  />
                  <Detail
                    label='Units'
                    value={selectedPurchase.dispensed_units}
                  />
                  <Detail
                    label='Batch'
                    value={selectedPurchase.batch_number ?? 'No linked batch'}
                  />
                  <Detail
                    label='Batch ID'
                    value={selectedPurchase.batch_id ?? '—'}
                  />
                  <Detail
                    label='Expiry'
                    value={
                      selectedPurchase.expiry_date
                        ? formatCalendarDate(selectedPurchase.expiry_date)
                        : '—'
                    }
                  />
                </DetailSection>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

function MetricCard({
  label,
  value,
  note,
}: {
  label: string
  value: string
  note: string
}) {
  return (
    <Card className='gap-2 py-4'>
      <CardContent className='px-4'>
        <p className='text-xs font-medium text-muted-foreground'>{label}</p>
        <p className='mt-2 truncate text-2xl font-semibold tracking-tight tabular-nums'>
          {value}
        </p>
        <p className='mt-1 text-xs text-muted-foreground'>{note}</p>
      </CardContent>
    </Card>
  )
}

function DetailSection({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className='space-y-3'>
      <h3 className='text-sm font-semibold'>{title}</h3>
      <div className='divide-y rounded-lg border px-3'>{children}</div>
    </section>
  )
}

function Detail({ label, value }: { label: string; value: string | number }) {
  return (
    <div className='flex items-start justify-between gap-4 py-3 text-sm'>
      <span className='text-muted-foreground'>{label}</span>
      <span className='max-w-[65%] text-right font-medium break-words tabular-nums'>
        {value}
      </span>
    </div>
  )
}
