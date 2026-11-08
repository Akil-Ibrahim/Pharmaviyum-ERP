import { useEffect, useState, type ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  ClipboardList,
  RefreshCw,
  ShoppingCart,
  UsersRound,
} from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

type DrugSalesCategory = {
  category: string
  lines: number
  packs: number
  revenue: number
}

type Summary = {
  as_of: string
  patients: { active: number }
  sales: { today: number; by_category: DrugSalesCategory[] }
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
    slow_moving: {
      id: number
      name: string
      packs_90d: number
      stock: number
      stock_value: number
    }[]
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

const money = (value: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'UAH',
    maximumFractionDigits: 0,
  }).format(value)

const number = (value: number) => new Intl.NumberFormat('en-US').format(value)

export function Dashboard() {
  const [data, setData] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    setError('')
    apiFetch<Summary>('/api/v1/dashboard/summary')
      .then(setData)
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : 'Unable to load analytics'
        )
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const inventory = data?.inventory
  const expiryTotal =
    (inventory?.expired ?? 0) +
    (inventory?.critical_expiry ?? 0) +
    (inventory?.warning_expiry ?? 0) +
    (inventory?.expiry_green ?? 0)

  const cards = [
    {
      label: 'Sales Today',
      value: money(data?.sales.today ?? 0),
      hint: 'Completed sales revenue for today',
      icon: ShoppingCart,
      tone: 'bg-amber-500/10 text-amber-600',
    },
    {
      label: 'Monthly Revenue',
      value: money(data?.revenue.month ?? 0),
      hint: `${number(data?.orders.completed_month ?? 0)} completed orders`,
      icon: Activity,
      tone: 'bg-orange-500/10 text-orange-600',
    },
    {
      label: 'Inventory Items',
      value: number(inventory?.items ?? 0),
      hint: `${money(inventory?.retail_value ?? 0)} retail value · ${number(inventory?.low_stock ?? 0)} low stock`,
      icon: Boxes,
      tone: 'bg-emerald-500/10 text-emerald-600',
    },
    {
      label: 'Active Patients',
      value: number(data?.patients.active ?? 0),
      hint: `${number(data?.prescriptions.month ?? 0)} prescriptions this month`,
      icon: UsersRound,
      tone: 'bg-violet-500/10 text-violet-600',
    },
  ]

  const categoryRows = data?.sales.by_category ?? []
  const categoryMaxRevenue = Math.max(
    ...categoryRows.map((row) => row.revenue),
    1
  )
  const categoryTotalRevenue = categoryRows.reduce(
    (total, row) => total + row.revenue,
    0
  )

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
          <section className='pharmacy-dashboard-hero relative flex flex-col gap-4 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-7'>
            <div className='relative z-10'>
              <div className='mb-2 flex items-center gap-2'>
                <Badge variant='secondary' className='rounded-md'>
                  PHARMAVIYUM ERP
                </Badge>
                <span className='text-xs text-muted-foreground'>
                  Pharmacy analytics
                </span>
              </div>
              <h1 className='text-2xl font-bold tracking-tight sm:text-3xl'>
                Welcome to your pharmacy
              </h1>
              <p className='mt-2 max-w-2xl text-sm text-muted-foreground'>
                Sales, inventory, expiry tracking, and key performance
                indicators in one workspace.
              </p>
            </div>
            <div className='relative z-10 flex shrink-0 gap-2'>
              <Button variant='outline' onClick={load} disabled={loading}>
                <RefreshCw
                  className={'mr-2 size-4 ' + (loading ? 'animate-spin' : '')}
                />
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

          {error && (
            <div
              role='alert'
              className='flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm'
            >
              <span>Unable to load live metrics: {error}</span>
              <Button variant='outline' size='sm' onClick={load}>
                Retry
              </Button>
            </div>
          )}

          <section>
            <div className='mb-3 flex items-end justify-between gap-3'>
              <div>
                <h2 className='text-base font-bold'>Pharmacy Performance</h2>
                <p className='text-sm text-muted-foreground'>
                  Live API data · no demo sales
                </p>
              </div>
              <span className='text-xs text-muted-foreground'>
                {data?.as_of
                  ? new Date(data.as_of).toLocaleString('en-US')
                  : '—'}
              </span>
            </div>
            <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
              {cards.map((card) => {
                const Icon = card.icon
                return (
                  <div
                    key={card.label}
                    className='min-w-0 rounded-xl border bg-card p-4 shadow-sm transition-shadow hover:shadow-md'
                  >
                    <div className='flex items-center justify-between gap-3'>
                      <p className='text-sm font-medium text-muted-foreground'>
                        {card.label}
                      </p>
                      <span
                        className={
                          'flex size-9 shrink-0 items-center justify-center rounded-lg ' +
                          card.tone
                        }
                      >
                        <Icon className='size-4' />
                      </span>
                    </div>
                    <p className='mt-3 truncate text-2xl font-semibold tracking-tight tabular-nums'>
                      {loading ? '—' : card.value}
                    </p>
                    <p className='mt-1 min-h-8 text-xs leading-4 text-muted-foreground'>
                      {card.hint}
                    </p>
                  </div>
                )
              })}
            </div>
          </section>

          <section className='grid gap-4 xl:grid-cols-2'>
            <div className='rounded-xl border bg-card p-4 shadow-sm sm:p-5'>
              <div className='mb-5 flex items-center justify-between gap-3'>
                <div>
                  <h2 className='font-semibold'>Sales Breakdown</h2>
                  <p className='text-xs text-muted-foreground'>
                    Rx and OTC · across recorded sales history
                  </p>
                </div>
                <Activity className='size-5 text-muted-foreground' />
              </div>
              {loading ? (
                <p className='py-6 text-center text-sm text-muted-foreground'>
                  Loading…
                </p>
              ) : categoryRows.length === 0 ? (
                <EmptyState text='No sales data available by category.' />
              ) : (
                <div className='space-y-5'>
                  {categoryRows.map((row) => (
                    <div key={row.category} className='space-y-2'>
                      <div className='flex items-center justify-between gap-3 text-sm'>
                        <span className='font-medium'>
                          {row.category === 'Rx'
                            ? 'Prescription (Rx)'
                            : row.category === 'OTC'
                              ? 'Over the Counter (OTC)'
                              : row.category}
                        </span>
                        <span className='font-semibold tabular-nums'>
                          {money(row.revenue)}
                        </span>
                      </div>
                      <div className='h-2.5 overflow-hidden rounded-full bg-muted'>
                        <div
                          className={
                            'h-full rounded-full ' +
                            (row.category === 'Rx'
                              ? 'bg-primary'
                              : 'bg-muted-foreground/60')
                          }
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(
                                100,
                                (row.revenue / categoryMaxRevenue) * 100
                              )
                            )}%`,
                          }}
                        />
                      </div>
                      <p className='text-xs text-muted-foreground'>
                        {number(row.lines)} lines · {number(row.packs)} packs
                      </p>
                    </div>
                  ))}
                  <div className='flex items-center justify-between border-t pt-3 text-sm'>
                    <span className='text-muted-foreground'>Total Revenue</span>
                    <span className='font-bold tabular-nums'>
                      {money(categoryTotalRevenue)}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className='rounded-xl border bg-card p-4 shadow-sm sm:p-5'>
              <div className='mb-5 flex items-center justify-between gap-3'>
                <div>
                  <h2 className='font-semibold'>Key Metrics</h2>
                  <p className='text-xs text-muted-foreground'>
                    Current calendar month
                  </p>
                </div>
                <ClipboardList className='size-5 text-muted-foreground' />
              </div>
              <div className='grid grid-cols-2 gap-3'>
                <div className='rounded-lg bg-muted/50 p-3'>
                  <p className='text-xs text-muted-foreground'>
                    Orders Created
                  </p>
                  <p className='mt-1 text-2xl font-semibold tabular-nums'>
                    {loading ? '—' : number(data?.orders.month ?? 0)}
                  </p>
                </div>
                <div className='rounded-lg bg-muted/50 p-3'>
                  <p className='text-xs text-muted-foreground'>
                    Orders Completed
                  </p>
                  <p className='mt-1 text-2xl font-semibold tabular-nums'>
                    {loading ? '—' : number(data?.orders.completed_month ?? 0)}
                  </p>
                </div>
                <div className='rounded-lg bg-muted/50 p-3'>
                  <p className='text-xs text-muted-foreground'>Prescriptions</p>
                  <p className='mt-1 text-2xl font-semibold tabular-nums'>
                    {loading ? '—' : number(data?.prescriptions.month ?? 0)}
                  </p>
                </div>
                <div className='rounded-lg bg-muted/50 p-3'>
                  <p className='text-xs text-muted-foreground'>Days of Stock</p>
                  <p className='mt-1 text-2xl font-semibold tabular-nums'>
                    {loading
                      ? '—'
                      : inventory?.days_on_hand == null
                        ? '—'
                        : number(inventory.days_on_hand)}
                  </p>
                </div>
              </div>
              <p className='mt-3 text-xs text-muted-foreground'>
                Days of stock are calculated from available inventory and actual
                dispensing over the last 30 days.
              </p>
            </div>
          </section>

          <section className='grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,.75fr)]'>
            <div className='rounded-2xl border bg-card p-4 sm:p-5'>
              <div className='mb-4 flex items-center justify-between gap-3'>
                <div>
                  <h2 className='font-bold'>Inventory Health</h2>
                  <p className='text-xs text-muted-foreground'>
                    Stock levels and expiry monitoring
                  </p>
                </div>
                <Boxes className='size-5 text-muted-foreground' />
              </div>
              <div className='grid gap-4 sm:grid-cols-2'>
                <div className='flex items-center gap-4'>
                  <RingMetric
                    progress={
                      inventory?.items
                        ? Math.max(
                            0,
                            100 - (inventory.low_stock / inventory.items) * 100
                          )
                        : 0
                    }
                    color='#10b981'
                    track='#d1fae5'
                    value={number(inventory?.items ?? 0)}
                    icon={<Boxes className='size-5' />}
                    size={104}
                  />
                  <div>
                    <p className='text-sm font-semibold'>Total Assortment</p>
                    <p className='mt-1 text-xs text-muted-foreground'>
                      Retail Value
                    </p>
                    <p className='mt-1 font-bold tabular-nums'>
                      {money(inventory?.retail_value ?? 0)}
                    </p>
                  </div>
                </div>
                <div className='flex items-center gap-4'>
                  <RingMetric
                    progress={
                      expiryTotal
                        ? ((inventory?.expiry_green ?? 0) / expiryTotal) * 100
                        : 0
                    }
                    color='#d946ef'
                    track='#fae8ff'
                    value={number(inventory?.expiry_green ?? 0)}
                    icon={<Activity className='size-5' />}
                    size={104}
                  />
                  <div>
                    <p className='text-sm font-semibold'>Expiry Status: Healthy</p>
                    <p className='mt-1 text-xs text-muted-foreground'>
                      Items with more than 12 months remaining
                    </p>
                    <p className='mt-1 font-bold'>
                      {number(inventory?.expiry_green ?? 0)} items
                    </p>
                  </div>
                </div>
              </div>
              <div className='mt-5 space-y-3'>
                {[
                  {
                    label: 'Expired',
                    value: inventory?.expired ?? 0,
                    color: '#ef4444',
                  },
                  {
                    label: 'Critical · within 3 months',
                    value: inventory?.critical_expiry ?? 0,
                    color: '#f97316',
                  },
                  {
                    label: 'Warning · 3–12 months',
                    value: inventory?.warning_expiry ?? 0,
                    color: '#f59e0b',
                  },
                  {
                    label: 'Healthy · over 12 months',
                    value: inventory?.expiry_green ?? 0,
                    color: '#10b981',
                  },
                ].map((row) => (
                  <div
                    key={row.label}
                    className='flex items-center gap-3 text-sm'
                  >
                    <span
                      className='size-2.5 rounded-full'
                      style={{ background: row.color }}
                    />
                    <span className='flex-1 text-muted-foreground'>
                      {row.label}
                    </span>
                    <span className='font-semibold tabular-nums'>
                      {number(row.value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className='rounded-2xl border bg-card p-4 sm:p-5'>
              <div className='mb-4 flex items-center justify-between'>
                <div>
                  <h2 className='font-bold'>Needs Attention</h2>
                  <p className='text-xs text-muted-foreground'>
                    Operational alerts
                  </p>
                </div>
                <Activity className='size-5 text-amber-500' />
              </div>
              <div className='space-y-3'>
                {[
                  {
                    label: 'Out of Stock',
                    value: data?.attention.stockout_items ?? 0,
                    detail: 'items out of stock',
                    color: 'bg-rose-500/10 text-rose-600',
                  },
                  {
                    label: 'Low Stock',
                    value: inventory?.low_stock ?? 0,
                    detail: 'items need replenishment',
                    color: 'bg-amber-500/10 text-amber-600',
                  },
                  {
                    label: 'Expiring Soon',
                    value: inventory?.critical_expiry ?? 0,
                    detail: 'items expiring within 3 months',
                    color: 'bg-orange-500/10 text-orange-600',
                  },
                  {
                    label: 'Slow Moving',
                    value: data?.attention.slow_moving_items ?? 0,
                    detail: 'items with no sales in 90 days',
                    color: 'bg-violet-500/10 text-violet-600',
                  },
                ].map((row) => (
                  <div
                    key={row.label}
                    className='flex items-center gap-3 rounded-xl border p-3'
                  >
                    <div
                      className={
                        'flex size-10 shrink-0 items-center justify-center rounded-xl text-lg font-bold ' +
                        row.color
                      }
                    >
                      {loading ? '…' : number(row.value)}
                    </div>
                    <div className='min-w-0'>
                      <p className='text-sm font-semibold'>{row.label}</p>
                      <p className='text-xs text-muted-foreground'>
                        {row.detail}
                      </p>
                    </div>
                    <ArrowDownRight className='ml-auto size-4 shrink-0 text-muted-foreground' />
                  </div>
                ))}
              </div>
              <Button variant='outline' className='mt-4 w-full' asChild>
                <Link to='/inventory'>
                  Go to Inventory
                  <ArrowRight className='ml-2 size-4' />
                </Link>
              </Button>
            </div>
          </section>

          <section className='grid gap-4 xl:grid-cols-2'>
            <div className='rounded-2xl border bg-card p-4 sm:p-5'>
              <div className='mb-4 flex items-center justify-between'>
                <div>
                  <h2 className='font-bold'>Top Products</h2>
                  <p className='text-xs text-muted-foreground'>
                    Based on actual sales
                  </p>
                </div>
                <ShoppingCart className='size-5 text-muted-foreground' />
              </div>
              {loading ? (
                <p className='py-6 text-center text-sm text-muted-foreground'>
                  Loading…
                </p>
              ) : !data?.top_products.length ? (
                <EmptyState text='No completed sales data yet.' />
              ) : (
                <div className='overflow-x-auto'>
                  <table className='w-full text-sm'>
                    <thead>
                      <tr className='border-b text-left text-muted-foreground'>
                        <th className='pb-2 font-medium'>Product</th>
                        <th className='pb-2 text-right font-medium'>Sold</th>
                        <th className='pb-2 text-right font-medium'>Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_products.slice(0, 6).map((product) => (
                        <tr key={product.id} className='border-b last:border-0'>
                          <td className='max-w-[240px] py-3 pr-3'>
                            <p className='truncate font-medium'>
                              {product.name}
                            </p>
                            <p className='text-xs text-muted-foreground'>
                              Stock: {number(product.stock)}
                            </p>
                          </td>
                          <td className='py-3 text-right tabular-nums'>
                            {number(product.packs)}
                          </td>
                          <td className='py-3 text-right font-semibold tabular-nums'>
                            {money(product.revenue)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className='rounded-2xl border bg-card p-4 sm:p-5'>
              <div className='mb-4 flex items-center justify-between'>
                <div>
                  <h2 className='font-bold'>Reorder Recommendations</h2>
                  <p className='text-xs text-muted-foreground'>
                    Items at or below reorder point
                  </p>
                </div>
                <ClipboardList className='size-5 text-muted-foreground' />
              </div>
              {loading ? (
                <p className='py-6 text-center text-sm text-muted-foreground'>
                  Loading…
                </p>
              ) : !data?.reorder_attention.length ? (
                <EmptyState text='No items are below the reorder point.' />
              ) : (
                <div className='space-y-3'>
                  {data.reorder_attention.slice(0, 5).map((item) => (
                    <div key={item.id} className='flex items-center gap-3'>
                      <div className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600'>
                        <Boxes className='size-4' />
                      </div>
                      <div className='min-w-0 flex-1'>
                        <p className='truncate text-sm font-semibold'>
                          {item.name}
                        </p>
                        <p className='text-xs text-muted-foreground'>
                          Available: {item.available_packs} packs · threshold
                          {' '}
                          {item.reorder_level}
                        </p>
                      </div>
                      <div className='text-right'>
                        <Badge
                          variant='outline'
                          className='border-amber-500/30 text-amber-600'
                        >
                          {item.days_on_hand == null
                            ? 'No demand'
                            : `${item.days_on_hand} days`}
                        </Badge>
                        <p className='mt-1 text-xs text-muted-foreground'>
                          {money(item.stock_value)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <Button variant='outline' className='mt-4 w-full' asChild>
                <Link to='/procurement'>
                  Open Procurement
                  <ArrowUpRight className='ml-2 size-4' />
                </Link>
              </Button>
            </div>
          </section>

          <p className='text-center text-xs text-muted-foreground'>
            Metrics reflect API data as of the last refresh.
            Empty values are never replaced with fabricated figures.
          </p>
        </div>
      </Main>
    </>
  )
}

function RingMetric({
  progress,
  color,
  track,
  value,
  icon,
  size = 88,
}: {
  progress: number
  color: string
  track: string
  value: string
  icon: ReactNode
  size?: number
}) {
  const radius = 34
  const circumference = 2 * Math.PI * radius
  const safeProgress = Math.max(0, Math.min(100, progress))

  return (
    <div
      className='relative shrink-0'
      style={{ width: size, height: size }}
      aria-label={`Metric ${value}`}
    >
      <svg
        viewBox='0 0 88 88'
        className='size-full -rotate-90'
        role='img'
        aria-hidden='true'
      >
        <circle
          cx='44'
          cy='44'
          r={radius}
          fill='none'
          stroke={track}
          strokeWidth='7'
        />
        <circle
          cx='44'
          cy='44'
          r={radius}
          fill='none'
          stroke={color}
          strokeWidth='7'
          strokeLinecap='round'
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - safeProgress / 100)}
          style={{ transition: 'stroke-dashoffset 500ms ease' }}
        />
      </svg>
      <div
        className='absolute inset-0 flex items-center justify-center'
        style={{ color }}
      >
        {icon}
      </div>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className='rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground'>
      {text}
    </div>
  )
}
