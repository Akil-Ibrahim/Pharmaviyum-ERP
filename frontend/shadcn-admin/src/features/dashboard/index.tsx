import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Boxes,
  CalendarClock,
  PackageSearch,
  RefreshCw,
  ShoppingCart,
  TrendingUp,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { apiFetch } from '@/lib/api-client'
import './dashboard.css'

type DashboardSummary = {
  as_of: string
  patients: { active: number }
  sales: {
    today: number
    revenue_30d: number
    previous_revenue_30d: number
    revenue_growth_30d: number | null
    average_order_value_30d: number
    orders_30d: number
    daily_revenue: { day: string; revenue: number }[]
    by_category: { category: string; lines: number; packs: number; revenue: number }[]
  }
  revenue: { month: number }
  orders: { month: number; completed_month: number }
  prescriptions: { month: number }
  inventory: {
    retail_value: number
    items: number
    low_stock: number
    days_on_hand: number | null
    expired: number
    critical_expiry: number
    warning_expiry: number
    expiry_green: number
  }
  attention: {
    stockout_items: number
    near_expiry_value: number
    slow_moving_items: number
    slow_moving_stock_value: number
  }
  top_products: {
    id: number
    name: string
    packs: number
    revenue: number
    stock: number
  }[]
  reorder_attention: {
    id: number
    name: string
    available_packs: number
    reorder_level: number
    packs_30d: number
    days_on_hand: number | null
    stock_value: number
  }[]
}

const number = (value: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)

const amount = (value: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)

const dateTime = (value: string) =>
  new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  loading,
}: {
  label: string
  value: string
  detail: string
  icon: typeof Activity
  loading: boolean
}) {
  return (
    <Card className='min-w-0 gap-3 py-5'>
      <CardHeader className='flex flex-row items-center justify-between gap-3 px-5 pb-0'>
        <CardDescription className='font-medium'>{label}</CardDescription>
        <span className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/8 text-primary'>
          <Icon className='size-4' aria-hidden='true' />
        </span>
      </CardHeader>
      <CardContent className='px-5'>
        {loading ? (
          <Skeleton className='h-8 w-28' />
        ) : (
          <p className='text-2xl font-semibold tracking-tight tabular-nums'>
            {value}
          </p>
        )}
        <p className='mt-1 min-h-8 text-xs leading-5 text-muted-foreground'>
          {detail}
        </p>
      </CardContent>
    </Card>
  )
}

function EmptyState({ children }: { children: string }) {
  return (
    <div className='flex min-h-32 items-center justify-center rounded-lg border border-dashed px-4 text-center text-sm text-muted-foreground'>
      {children}
    </div>
  )
}

export function Dashboard() {
  const { data, error, isError, isPending, isFetching, refetch } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => apiFetch<DashboardSummary>('/api/v1/dashboard/summary'),
    staleTime: 60_000,
    retry: 1,
  })

  const categories = data?.sales.by_category ?? []
  const revenueTrend = data?.sales.daily_revenue ?? []
  const revenueGrowth = data?.sales.revenue_growth_30d
  const revenueGrowthLabel =
    revenueGrowth == null
      ? 'Comparison unavailable — no prior-period sales'
      : `${revenueGrowth > 0 ? '+' : ''}${revenueGrowth}% vs previous 30 days · ${amount(data?.sales.previous_revenue_30d ?? 0)} prior revenue`
  const expiryRows = [
    { label: 'Expired', value: data?.inventory.expired ?? 0, variant: 'destructive' as const },
    { label: 'Expiring within 3 months', value: data?.inventory.critical_expiry ?? 0, variant: 'destructive' as const },
    { label: 'Expiring in 3–12 months', value: data?.inventory.warning_expiry ?? 0, variant: 'secondary' as const },
    { label: 'More than 12 months remaining', value: data?.inventory.expiry_green ?? 0, variant: 'outline' as const },
  ]

  return (
    <>
      <Header>
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>
      <Main>
        <div className='pharmaviyum-dashboard pharmacy-dashboard-page space-y-5'>
          <section className='pharmacy-dashboard-hero relative flex flex-col gap-4 rounded-xl border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-7'>
            <div className='relative z-10 min-w-0'>
              <div className='mb-2 flex items-center gap-2'>
                <Badge variant='secondary'>PHARMAVIYUM ERP</Badge>
                <span className='text-xs text-muted-foreground'>Operations overview</span>
              </div>
              <h1 className='text-2xl font-semibold tracking-tight sm:text-3xl'>
                Pharmacy Dashboard
              </h1>
              <p className='mt-2 max-w-2xl text-sm text-muted-foreground'>
                A live overview of sales, stock health, expiry risk, and pharmacy activity.
              </p>
              {data?.as_of && (
                <p className='mt-3 text-xs text-muted-foreground'>
                  Updated {dateTime(data.as_of)}
                </p>
              )}
            </div>
            <div className='relative z-10 flex shrink-0 flex-wrap gap-2'>
              <Button variant='outline' onClick={() => void refetch()} disabled={isFetching}>
                <RefreshCw className={`mr-2 size-4 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button asChild>
                <Link to='/pos'>
                  <ShoppingCart className='mr-2 size-4' />
                  Open POS
                </Link>
              </Button>
            </div>
          </section>

          {isError && (
            <div role='alert' className='flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm'>
              <span>{error instanceof Error ? error.message : 'Unable to load dashboard metrics.'}</span>
              <Button variant='outline' size='sm' onClick={() => void refetch()}>Retry</Button>
            </div>
          )}

          <section aria-label='Pharmacy key performance indicators' className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
            <MetricCard label='Sales Today' value={amount(data?.sales.today ?? 0)} detail='Realized sales recorded today' icon={ShoppingCart} loading={isPending} />
            <MetricCard label='Revenue (30 Days)' value={amount(data?.sales.revenue_30d ?? 0)} detail={revenueGrowthLabel} icon={TrendingUp} loading={isPending} />
            <MetricCard label='Average Order Value' value={amount(data?.sales.average_order_value_30d ?? 0)} detail='Average completed receipt value over 30 days' icon={Boxes} loading={isPending} />
            <MetricCard label='Orders (30 Days)' value={number(data?.sales.orders_30d ?? 0)} detail='Distinct receipts with realized sales' icon={CalendarClock} loading={isPending} />
          </section>

          <section className='grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,.8fr)]'>
            <Card className='min-w-0'>
              <CardHeader>
                <CardTitle>Revenue Trend</CardTitle>
                <CardDescription>Daily realized revenue over the last 30 days</CardDescription>
              </CardHeader>
              <CardContent>
                {isPending ? (
                  <Skeleton className='h-64 w-full' />
                ) : revenueTrend.length === 0 ? (
                  <EmptyState>No realized sales were recorded in the last 30 days.</EmptyState>
                ) : (
                  <div className='h-64 w-full' role='img' aria-label='Daily realized revenue for the last 30 days'>
                    <ResponsiveContainer width='100%' height='100%'>
                      <LineChart data={revenueTrend} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                        <CartesianGrid strokeDasharray='3 3' vertical={false} className='stroke-border' />
                        <XAxis dataKey='day' tickLine={false} axisLine={false} fontSize={11} minTickGap={24} tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                        <YAxis tickLine={false} axisLine={false} width={64} fontSize={11} tickFormatter={amount} />
                        <Tooltip labelFormatter={(value) => new Date(String(value)).toLocaleDateString('en-US', { dateStyle: 'medium' })} formatter={(value) => amount(Number(value))} />
                        <Line type='monotone' dataKey='revenue' stroke='var(--primary)' strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Inventory Health</CardTitle>
                <CardDescription>Current stock and expiry monitoring</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='grid grid-cols-2 gap-3'>
                  <div className='rounded-lg bg-muted/50 p-3'>
                    <p className='text-xs text-muted-foreground'>Retail value</p>
                    <p className='mt-1 text-xl font-semibold tabular-nums'>{isPending ? '—' : amount(data?.inventory.retail_value ?? 0)}</p>
                  </div>
                  <div className='rounded-lg bg-muted/50 p-3'>
                    <p className='text-xs text-muted-foreground'>Stock coverage</p>
                    <p className='mt-1 text-xl font-semibold tabular-nums'>{isPending || data?.inventory.days_on_hand == null ? '—' : `${number(data.inventory.days_on_hand)} days`}</p>
                  </div>
                </div>
                <div className='space-y-3'>
                  {expiryRows.map((row) => (
                    <div key={row.label} className='flex items-center justify-between gap-3 text-sm'>
                      <span className='text-muted-foreground'>{row.label}</span>
                      <Badge variant={row.variant}>{isPending ? '—' : number(row.value)}</Badge>
                    </div>
                  ))}
                </div>
                <Button variant='outline' className='w-full' asChild>
                  <Link to='/inventory'>
                    View inventory
                    <ArrowRight className='ml-2 size-4' />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </section>

          <section className='grid min-w-0 gap-4 xl:grid-cols-3'>
            <Card className='min-w-0'>
              <CardHeader>
                <CardTitle>Sales Mix</CardTitle>
                <CardDescription>Realized revenue by prescription category this month</CardDescription>
              </CardHeader>
              <CardContent>
                {isPending ? (
                  <Skeleton className='h-48 w-full' />
                ) : categories.length === 0 ? (
                  <EmptyState>No sales category data is available yet.</EmptyState>
                ) : (
                  <>
                    <div className='h-48 w-full' role='img' aria-label='Monthly revenue by prescription category'>
                      <ResponsiveContainer width='100%' height='100%'>
                        <BarChart data={categories} layout='vertical' margin={{ top: 4, right: 8, bottom: 4, left: 4 }}>
                          <CartesianGrid strokeDasharray='3 3' horizontal={false} className='stroke-border' />
                          <XAxis type='number' tickLine={false} axisLine={false} tickFormatter={amount} fontSize={11} />
                          <YAxis type='category' dataKey='category' tickLine={false} axisLine={false} width={42} fontSize={11} />
                          <Tooltip formatter={(value) => amount(Number(value))} />
                          <Bar dataKey='revenue' fill='var(--primary)' radius={[0, 5, 5, 0]} maxBarSize={28} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className='mt-3 flex flex-wrap gap-x-4 gap-y-2 border-t pt-3 text-xs text-muted-foreground'>
                      <span>{number(categories.reduce((sum, row) => sum + row.lines, 0))} sales lines</span>
                      <span>{number(categories.reduce((sum, row) => sum + row.packs, 0))} packs dispensed</span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
            <Card className='min-w-0'>
              <CardHeader className='flex flex-row items-start justify-between gap-3'>
                <div>
                  <CardTitle>Top Selling Medicines</CardTitle>
                  <CardDescription>Products ranked by dispensed packs</CardDescription>
                </div>
                <PackageSearch className='size-5 text-muted-foreground' aria-hidden='true' />
              </CardHeader>
              <CardContent>
                {isPending ? (
                  <div className='space-y-3'><Skeleton className='h-9 w-full' /><Skeleton className='h-9 w-full' /><Skeleton className='h-9 w-full' /></div>
                ) : !data?.top_products.length ? (
                  <EmptyState>No product sales have been recorded yet.</EmptyState>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Medicine</TableHead>
                        <TableHead className='text-right'>Packs</TableHead>
                        <TableHead className='text-right'>Stock units</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.top_products.slice(0, 5).map((product) => (
                        <TableRow key={product.id}>
                          <TableCell className='max-w-48 truncate font-medium'>{product.name}</TableCell>
                          <TableCell className='text-right'>{number(product.packs)}</TableCell>
                          <TableCell className='text-right'>{number(product.stock)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card className='min-w-0'>
              <CardHeader className='flex flex-row items-start justify-between gap-3'>
                <div>
                  <CardTitle>Reorder Attention</CardTitle>
                  <CardDescription>Products at or below their configured reorder level</CardDescription>
                </div>
                <CalendarClock className='size-5 text-muted-foreground' aria-hidden='true' />
              </CardHeader>
              <CardContent>
                {isPending ? (
                  <div className='space-y-3'><Skeleton className='h-9 w-full' /><Skeleton className='h-9 w-full' /><Skeleton className='h-9 w-full' /></div>
                ) : !data?.reorder_attention.length ? (
                  <EmptyState>No products currently require reorder attention.</EmptyState>
                ) : (
                  <div className='space-y-3'>
                    {data.reorder_attention.map((product) => (
                      <div key={product.id} className='flex items-center justify-between gap-3 border-b pb-3 last:border-0 last:pb-0'>
                        <div className='min-w-0'>
                          <p className='truncate text-sm font-medium'>{product.name}</p>
                          <p className='mt-1 text-xs text-muted-foreground'>Reorder level: {number(product.reorder_level)} packs · 30-day demand: {number(product.packs_30d)} packs</p>
                        </div>
                        <Badge variant='secondary' className='shrink-0'>{number(product.available_packs)} packs left</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          <Card className='pharmacy-priority-panel'>
            <CardHeader className='flex flex-row items-start justify-between gap-3'>
              <div>
                <CardTitle>Needs Attention</CardTitle>
                <CardDescription>Operational signals that may need a pharmacist or manager review</CardDescription>
              </div>
              <AlertTriangle className='size-5 text-muted-foreground' aria-hidden='true' />
            </CardHeader>
            <CardContent className='grid gap-3 sm:grid-cols-2 xl:grid-cols-4'>
              {[
                { label: 'Out of stock', value: data?.attention.stockout_items ?? 0, note: 'Products with no available units' },
                { label: 'Low stock', value: data?.inventory.low_stock ?? 0, note: 'Products at or below reorder level' },
                { label: 'Expiry risk', value: (data?.inventory.expired ?? 0) + (data?.inventory.critical_expiry ?? 0), note: 'Expired or expiring within 3 months' },
                { label: 'Slow moving', value: data?.attention.slow_moving_items ?? 0, note: 'Products without recorded sales in 90 days' },
              ].map((item) => (
                <div key={item.label} className='rounded-lg border p-3'>
                  <p className='text-sm font-medium'>{item.label}</p>
                  <p className='mt-2 text-2xl font-semibold tabular-nums'>{isPending ? '—' : number(item.value)}</p>
                  <p className='mt-1 text-xs leading-5 text-muted-foreground'>{item.note}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className='flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground'>
            <span><Activity className='mr-1 inline size-3.5' />Operational metrics only. Patient-level purchase and medication history are not included.</span>
            <span>{data?.as_of ? `Data timestamp: ${dateTime(data.as_of)}` : 'Live API data'}</span>
          </div>
        </div>
      </Main>
    </>
  )
}
