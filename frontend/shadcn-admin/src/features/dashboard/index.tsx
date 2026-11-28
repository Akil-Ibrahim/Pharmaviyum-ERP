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
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  ResponsiveContainer,
  RadialBar,
  RadialBarChart,
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
    expiry_tracked: number
    expiry_red: number
    expiry_yellow: number
    expiry_green: number
    expired: number
    critical_expiry: number
    warning_expiry: number
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

function completeDailyRevenue(
  points: { day: string; revenue: number }[],
  asOf: string
) {
  const revenueByDay = new Map(
    points.map((point) => [point.day.slice(0, 10), point.revenue])
  )
  const end = new Date(asOf)
  const endUtc = Date.UTC(
    end.getUTCFullYear(),
    end.getUTCMonth(),
    end.getUTCDate()
  )

  return Array.from({ length: 30 }, (_, index) => {
    const date = new Date(endUtc - (29 - index) * 24 * 60 * 60 * 1000)
    const day = date.toISOString().slice(0, 10)
    return { day, revenue: revenueByDay.get(day) ?? 0 }
  })
}


function SalesMixRadialCard({
  categories,
  loading,
}: {
  categories: DashboardSummary['sales']['by_category']
  loading: boolean
}) {
  const rxRevenue = categories
    .filter((category) => category.category === 'Rx')
    .reduce((sum, category) => sum + category.revenue, 0)
  const otcRevenue = categories
    .filter((category) => category.category === 'OTC')
    .reduce((sum, category) => sum + category.revenue, 0)
  const totalRevenue = rxRevenue + otcRevenue
  const rxShare = totalRevenue > 0 ? (rxRevenue / totalRevenue) * 100 : 0
  const otcShare = totalRevenue > 0 ? (otcRevenue / totalRevenue) * 100 : 0

  return (
    <Card className='min-w-0'>
      <CardHeader>
        <CardTitle>Sales Mix</CardTitle>
        <CardDescription>Rx and OTC share of realized monthly revenue</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className='mx-auto h-64 w-full max-w-[260px] rounded-full' />
        ) : totalRevenue === 0 ? (
          <EmptyState>No sales category data is available yet.</EmptyState>
        ) : (
          <div className='flex flex-col items-center gap-4 sm:flex-row sm:justify-center'>
            <div
              className='relative h-64 w-full max-w-[260px] shrink-0'
              role='img'
              aria-label={`Monthly sales mix: Rx ${rxShare.toFixed(1)} percent, OTC ${otcShare.toFixed(1)} percent. Total revenue ${amount(totalRevenue)}.`}
            >
              <ResponsiveContainer width='100%' height='100%'>
                <RadialBarChart
                  data={[{ rx: rxShare, otc: otcShare }]}
                  innerRadius='18%'
                  outerRadius='88%'
                  barSize={13}
                  startAngle={90}
                  endAngle={-270}
                >
                  <PolarAngleAxis type='number' domain={[0, 100]} tick={false} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(1)}% of revenue`} />
                  <RadialBar dataKey='rx' name='Rx' fill='var(--chart-1)' background cornerRadius={7} />
                  <RadialBar dataKey='otc' name='OTC' fill='var(--chart-2)' background cornerRadius={7} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className='pointer-events-none absolute inset-0 flex flex-col items-center justify-center'>
                <span className='text-2xl font-semibold tracking-tight tabular-nums'>
                  {amount(totalRevenue)}
                </span>
                <span className='text-xs text-muted-foreground'>Total revenue</span>
              </div>
            </div>
            <div className='grid w-full gap-3 sm:max-w-44'>
              {[
                { label: 'Prescription (Rx)', revenue: rxRevenue, share: rxShare, fill: 'var(--chart-1)' },
                { label: 'Over the counter (OTC)', revenue: otcRevenue, share: otcShare, fill: 'var(--chart-2)' },
              ].map((item) => (
                <div key={item.label} className='flex items-center justify-between gap-3 text-sm'>
                  <span className='flex min-w-0 items-center gap-2 text-muted-foreground'>
                    <span className='size-2.5 shrink-0 rounded-full' style={{ backgroundColor: item.fill }} aria-hidden='true' />
                    <span>{item.label}</span>
                  </span>
                  <span className='text-right font-semibold tabular-nums'>
                    {item.share.toFixed(1)}%
                    <span className='block text-xs font-normal text-muted-foreground'>{amount(item.revenue)}</span>
                  </span>
                </div>
              ))}
              <div className='border-t pt-3 text-xs text-muted-foreground'>
                {number(categories.reduce((sum, row) => sum + row.lines, 0))} sales lines · {number(categories.reduce((sum, row) => sum + row.packs, 0))} packs dispensed
              </div>
            </div>
          </div>
        )}
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

function ExpiryRadialCard({
  tracked,
  red,
  yellow,
  green,
  loading,
}: {
  tracked: number
  red: number
  yellow: number
  green: number
  loading: boolean
}) {
  const redShare = tracked > 0 ? (red / tracked) * 100 : 0
  const yellowShare = tracked > 0 ? (yellow / tracked) * 100 : 0
  const greenShare = tracked > 0 ? (green / tracked) * 100 : 0

  return (
    <Card className='min-w-0'>
      <CardHeader>
        <CardTitle>Inventory Expiry Health</CardTitle>
        <CardDescription>
          Concentric rings show the share of tracked lots in each expiry window
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className='mx-auto h-64 w-full max-w-[260px] rounded-full' />
        ) : tracked === 0 ? (
          <EmptyState>No expiry-dated inventory lots are available.</EmptyState>
        ) : (
          <div className='flex flex-col items-center gap-4 sm:flex-row sm:justify-center'>
            <div
              className='relative h-64 w-full max-w-[260px] shrink-0'
              role='img'
              aria-label={`Inventory expiry health: ${red} expired or within 90 days, ${yellow} with 91 to 365 days remaining, and ${green} with more than 365 days remaining, out of ${tracked} tracked lots.`}
            >
              <ResponsiveContainer width='100%' height='100%'>
                <RadialBarChart
                  data={[{ critical: redShare, warning: yellowShare, healthy: greenShare }]}
                  innerRadius='18%'
                  outerRadius='88%'
                  barSize={11}
                  startAngle={90}
                  endAngle={-270}
                >
                  <PolarAngleAxis type='number' domain={[0, 100]} tick={false} />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(1)}% of tracked lots`} />
                  <RadialBar dataKey='critical' name='Expired / within 90 days' fill='var(--chart-1)' background cornerRadius={7} />
                  <RadialBar dataKey='warning' name='91–365 days remaining' fill='var(--chart-2)' background cornerRadius={7} />
                  <RadialBar dataKey='healthy' name='More than 365 days' fill='var(--chart-3)' background cornerRadius={7} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className='pointer-events-none absolute inset-0 flex flex-col items-center justify-center'>
                <span className='text-3xl font-semibold tracking-tight tabular-nums'>
                  {number(tracked)}
                </span>
                <span className='text-xs text-muted-foreground'>Tracked lots</span>
              </div>
            </div>
            <div className='grid w-full gap-3 sm:max-w-52'>
              {[
                { name: 'Expired / within 90 days', value: red, share: redShare, fill: 'var(--chart-1)' },
                { name: '91–365 days remaining', value: yellow, share: yellowShare, fill: 'var(--chart-2)' },
                { name: 'More than 365 days', value: green, share: greenShare, fill: 'var(--chart-3)' },
              ].map((item) => (
                <div key={item.name} className='flex items-center justify-between gap-3 text-sm'>
                  <span className='flex min-w-0 items-center gap-2 text-muted-foreground'>
                    <span className='size-2.5 shrink-0 rounded-full' style={{ backgroundColor: item.fill }} aria-hidden='true' />
                    <span>{item.name}</span>
                  </span>
                  <span className='text-right font-semibold tabular-nums'>
                    {item.share.toFixed(1)}%
                    <span className='block text-xs font-normal text-muted-foreground'>{number(item.value)} lots</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        <p className='mt-3 text-center text-xs text-muted-foreground'>
          Each ring is normalized against all tracked expiry-dated lots.
        </p>
      </CardContent>
    </Card>
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
  const revenueTrend = data
    ? completeDailyRevenue(data.sales.daily_revenue, data.as_of)
    : []
  const revenueGrowth = data?.sales.revenue_growth_30d
  const revenueGrowthLabel =
    revenueGrowth == null
      ? 'Comparison unavailable — no prior-period sales'
      : `${revenueGrowth > 0 ? '+' : ''}${revenueGrowth}% vs previous 30 days · ${amount(data?.sales.previous_revenue_30d ?? 0)} prior revenue`
  const expiryRows = [
    { label: 'Missing expiry date', value: data?.inventory.missing_expiry ?? 0, variant: 'destructive' as const },
    { label: 'Expired', value: data?.inventory.expired ?? 0, variant: 'destructive' as const },
    { label: 'Expiring within 90 days', value: data?.inventory.critical_expiry ?? 0, variant: 'destructive' as const },
    { label: 'Expiring in 91–365 days', value: data?.inventory.warning_expiry ?? 0, variant: 'secondary' as const },
    { label: 'More than 365 days remaining', value: data?.inventory.expiry_green ?? 0, variant: 'outline' as const },
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
                ) : data?.sales.orders_30d === 0 ? (
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
                    <p className='text-xs text-muted-foreground'>Sellable retail value</p>
                    <p className='mt-1 text-xl font-semibold tabular-nums'>{isPending ? '—' : amount(data?.inventory.retail_value ?? 0)}</p>
                    <p className='mt-1 text-xs text-muted-foreground'>Unexpired available stock at retail price, not acquisition cost</p>
                  </div>
                  <div className='rounded-lg bg-muted/50 p-3'>
                    <p className='text-xs text-muted-foreground'>Median Stock Cover</p>
                    <p className='mt-1 text-xl font-semibold tabular-nums'>{isPending || data?.inventory.days_on_hand == null ? '—' : `${number(data.inventory.days_on_hand)} days`}</p>
                    <p className='mt-1 text-xs text-muted-foreground'>Median days on hand for in-stock SKUs using unexpired stock and 30-day dispensing</p>
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

          <section aria-label='Inventory expiry radial analytics' className='grid min-w-0 gap-4 xl:grid-cols-2'>
            <ExpiryRadialCard
              tracked={data?.inventory.expiry_tracked ?? 0}
              red={data?.inventory.expiry_red ?? 0}
              yellow={data?.inventory.expiry_yellow ?? 0}
              green={data?.inventory.expiry_green ?? 0}
              loading={isPending}
            />
            <Card className='min-w-0'>
              <CardHeader>
                <CardTitle>Expiry Risk Summary</CardTitle>
                <CardDescription>Counts behind the radial inventory view</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                {[
                  { label: 'Expired', value: data?.inventory.expired ?? 0, note: 'Lots already past expiry' },
                  { label: 'Critical', value: data?.inventory.critical_expiry ?? 0, note: 'Expiry within 90 days' },
                  { label: 'Warning', value: data?.inventory.warning_expiry ?? 0, note: 'Expiry in 91–365 days' },
                  { label: 'Healthy horizon', value: data?.inventory.expiry_green ?? 0, note: 'More than 365 days remaining' },
                ].map((item) => (
                  <div key={item.label} className='flex items-center justify-between gap-3 border-b pb-3 last:border-0 last:pb-0'>
                    <div>
                      <p className='text-sm font-medium'>{item.label}</p>
                      <p className='text-xs text-muted-foreground'>{item.note}</p>
                    </div>
                    <span className='text-lg font-semibold tabular-nums'>{isPending ? '—' : number(item.value)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </section>

          <section className='grid min-w-0 gap-4 xl:grid-cols-3'>
            <SalesMixRadialCard categories={categories} loading={isPending} />
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
                { label: 'Expiry risk', value: (data?.inventory.expired ?? 0) + (data?.inventory.critical_expiry ?? 0), note: 'Expired or expiring within 90 days' },
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
