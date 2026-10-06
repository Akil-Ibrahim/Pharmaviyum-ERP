import { useEffect, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  Boxes,
  FileText,
  Pill,
  Receipt,
  Truck,
  Users,
  Wallet,
  type LucideIcon,
} from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

type DashboardSummary = {
  as_of: string
  patients: { active: number }
  sales: { today: number }
  revenue: { month: number }
  orders: { month: number; completed_month: number }
  prescriptions: { month: number }
  inventory: {
    retail_value: number
    low_stock: number
    expired: number
    critical_expiry: number
    warning_expiry: number
  }
}

const previewDonuts: {
  title: string
  total: string
  items: [string, number][]
}[] = [
  {
    title: 'Sales by category',
    total: '$128K',
    items: [
      ['Prescription', 42],
      ['OTC', 31],
      ['Supplements', 17],
      ['Devices', 10],
    ],
  },
  {
    title: 'Inventory status',
    total: '4,821',
    items: [
      ['Good', 68],
      ['Warning', 19],
      ['Critical', 9],
      ['Expired', 4],
    ],
  },
  {
    title: 'Order status',
    total: '1,284',
    items: [
      ['Completed', 74],
      ['Processing', 13],
      ['Pending', 8],
      ['Cancelled', 5],
    ],
  },
]

const pipelines: {
  title: string
  icon: LucideIcon
  stages: [string, number][]
}[] = [
  {
    title: 'Procurement',
    icon: Truck,
    stages: [
      ['Ordered', 28],
      ['Shipped', 16],
      ['Received', 11],
      ['Stock', 8],
    ],
  },
  {
    title: 'Prescriptions',
    icon: FileText,
    stages: [
      ['Received', 54],
      ['Validated', 41],
      ['Dispensing', 29],
      ['Completed', 23],
    ],
  },
  {
    title: 'Orders / POS',
    icon: Receipt,
    stages: [
      ['Created', 36],
      ['Processing', 27],
      ['Paid', 22],
      ['Completed', 19],
    ],
  },
  {
    title: 'Transfers',
    icon: Boxes,
    stages: [
      ['Requested', 14],
      ['Approved', 10],
      ['In transit', 7],
      ['Received', 5],
    ],
  },
]

const statistics: [string, string, string, 'up' | 'down'][] = [
  ['Orders', '1,284', '+12.4%', 'up'],
  ['Prescriptions', '846', '92% completed', 'up'],
  ['Products', '4,821', '127 low stock', 'down'],
  ['Inventory value', '$284K', '94% healthy stock', 'up'],
  ['Expiring soon', '86', '12 critical', 'down'],
  ['Transfers', '42', '8 pending', 'down'],
]

const monthlyRevenue = [42, 49, 46, 61, 58, 72, 68, 81, 76, 89, 84, 96]

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)

  useEffect(() => {
    apiFetch<DashboardSummary>('/api/v1/dashboard/summary')
      .then(setSummary)
      .catch(() => setSummary(null))
  }, [])

  return (
    <>
      <Header>
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between'>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>
              Pharmacy Dashboard
            </h1>
            <p className='text-muted-foreground'>
              Pharmacy operations, performance, and workflow overview.
            </p>
          </div>
          <span className='w-fit rounded-full border bg-muted/40 px-3 py-1 text-xs text-muted-foreground'>
            KPI live · operational metrics coming next
          </span>
        </div>

        <div className='space-y-6'>
          <section className='grid gap-4 md:grid-cols-3'>
            <KpiCard
              label='Patients'
              value={summary ? summary.patients.active.toLocaleString() : '—'}
              detail={summary ? 'Active patient profiles' : 'Awaiting API data'}
              icon={Users}
            />
            <KpiCard
              label='Sales'
              value={
                summary
                  ? formatCurrency(summary.sales.today)
                  : '—'
              }
              detail={summary ? 'Today · realized sales' : 'Awaiting API data'}
              icon={Receipt}
            />
            <KpiCard
              label='Revenue'
              value={
                summary
                  ? formatCurrency(summary.revenue.month)
                  : '—'
              }
              detail={summary ? 'This month · realized revenue' : 'Awaiting API data'}
              icon={Wallet}
            />
          </section>

          <section className='grid gap-4 xl:grid-cols-3'>
            {previewDonuts.map((donut) => (
              <DonutCard key={donut.title} {...donut} />
            ))}
          </section>

          <section className='grid gap-4 xl:grid-cols-2'>
            {pipelines.map((pipeline) => (
              <PipelineCard key={pipeline.title} {...pipeline} />
            ))}
          </section>

          <section className='rounded-2xl border bg-card p-5 shadow-sm'>
            <div className='mb-5 flex items-center justify-between'>
              <div>
                <h2 className='font-semibold'>Sales & Revenue</h2>
                <p className='text-xs text-muted-foreground'>
                  Monthly performance · preview data
                </p>
              </div>
              <div className='rounded-lg border bg-muted/30 p-1 text-xs'>
                <span className='rounded-md bg-background px-2 py-1 font-medium shadow-sm'>
                  12M
                </span>
                <span className='px-2 py-1 text-muted-foreground'>90D</span>
                <span className='px-2 py-1 text-muted-foreground'>30D</span>
              </div>
            </div>
            <div className='flex h-56 items-end gap-2'>
              {monthlyRevenue.map((height, index) => (
                <div key={index} className='flex h-full flex-1 items-end'>
                  <div
                    className='w-full rounded-t-md bg-primary/80 transition-all hover:bg-primary'
                    style={{ height: height + '%' }}
                  />
                </div>
              ))}
            </div>
            <div className='mt-3 flex justify-between text-[11px] text-muted-foreground'>
              {[
                'Jan',
                'Feb',
                'Mar',
                'Apr',
                'May',
                'Jun',
                'Jul',
                'Aug',
                'Sep',
                'Oct',
                'Nov',
                'Dec',
              ].map((month) => (
                <span key={month}>{month}</span>
              ))}
            </div>
          </section>

          <section>
            <div className='mb-3'>
              <h2 className='font-semibold'>Operational Statistics</h2>
              <p className='text-xs text-muted-foreground'>
                Compact operational signals for daily pharmacy management.
              </p>
            </div>
            <div className='grid gap-3 sm:grid-cols-2 xl:grid-cols-3'>
              {statistics.map(([label, value, detail, direction]) => (
                <div
                  key={label}
                  className='rounded-xl border bg-card p-4 shadow-sm'
                >
                  <div className='flex items-center justify-between'>
                    <span className='text-sm text-muted-foreground'>
                      {label}
                    </span>
                    {direction === 'up' ? (
                      <ArrowUpRight className='size-4 text-emerald-600' />
                    ) : (
                      <ArrowDownRight className='size-4 text-amber-600' />
                    )}
                  </div>
                  <div className='mt-2 text-2xl font-semibold tracking-tight'>
                    {value}
                  </div>
                  <div className='mt-1 text-xs text-muted-foreground'>
                    {detail}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className='grid gap-4 xl:grid-cols-2'>
            <DataTable
              title='Top Products'
              columns={['Product', 'Units', 'Revenue', 'Stock']}
              rows={[
                ['Omeprazole 20 mg', '486', '$12.4K', '124'],
                ['Paracetamol 500 mg', '421', '$8.7K', '318'],
                ['Amoxicillin 500 mg', '286', '$7.9K', '96'],
                ['Ibuprofen 400 mg', '254', '$6.8K', '142'],
              ]}
            />
            <DataTable
              title='Operational Alerts'
              columns={['Alert', 'Count', 'Priority', 'Status']}
              rows={[
                ['Critical expiry', '12', 'High', 'Review'],
                ['Low stock', '127', 'Medium', 'Monitor'],
                ['Pending receiving', '11', 'Medium', 'Process'],
                ['Pending transfers', '8', 'Low', 'Review'],
              ]}
            />
          </section>

          <section className='rounded-2xl border bg-muted/20 p-5'>
            <div className='flex items-start gap-3'>
              <div className='rounded-lg bg-primary/10 p-2 text-primary'>
                <Pill className='size-5' />
              </div>
              <div>
                <h2 className='font-semibold'>Mortarium AI</h2>
                <p className='mt-1 text-sm text-muted-foreground'>
                  AI usage, RAG queries, validation, and safety events will be
                  connected to this dashboard after the backend metrics layer is
                  implemented.
                </p>
              </div>
            </div>
          </section>
        </div>
      </Main>
    </>
  )
}

function formatCurrency(value: number) {
  return value.toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  })
}

function KpiCard({
  label,
  value,
  detail,
  icon: Icon,
  trend,
}: {
  label: string
  value: string
  detail: string
  icon: LucideIcon
  trend?: string
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='flex items-center justify-between'>
        <div className='rounded-lg bg-primary/10 p-2 text-primary'>
          <Icon className='size-5' />
        </div>
        {trend && (
          <span className='flex items-center gap-1 text-xs font-medium text-emerald-600'>
            <ArrowUpRight className='size-3.5' />
            {trend}
          </span>
        )}
      </div>
      <p className='mt-4 text-sm text-muted-foreground'>{label}</p>
      <p className='mt-1 text-3xl font-bold tracking-tight'>{value}</p>
      <p className='mt-1 text-xs text-muted-foreground'>{detail}</p>
    </div>
  )
}

function DonutCard({
  title,
  total,
  items,
}: {
  title: string
  total: string
  items: [string, number][]
}) {
  const palette = [
    'hsl(var(--primary))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
  ]
  const stops = items.reduce<string[]>((acc, [, value], index) => {
    const start = items
      .slice(0, index)
      .reduce((sum, [, current]) => sum + current, 0)
    acc.push(palette[index] + ' ' + start + '% ' + (start + value) + '%')
    return acc
  }, [])

  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='mb-4'>
        <h2 className='font-semibold'>{title}</h2>
        <p className='text-xs text-muted-foreground'>Preview distribution</p>
      </div>
      <div className='flex items-center gap-5'>
        <div
          className='relative grid size-28 shrink-0 place-items-center rounded-full'
          style={{ background: 'conic-gradient(' + stops.join(', ') + ')' }}
        >
          <div className='grid size-18 place-items-center rounded-full bg-card'>
            <span className='text-sm font-bold'>{total}</span>
          </div>
        </div>
        <div className='min-w-0 flex-1 space-y-2'>
          {items.map(([label, value]) => (
            <div
              key={label}
              className='flex items-center justify-between gap-3 text-xs'
            >
              <span className='truncate text-muted-foreground'>{label}</span>
              <span className='font-medium'>{value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PipelineCard({
  title,
  icon: Icon,
  stages,
}: {
  title: string
  icon: LucideIcon
  stages: [string, number][]
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='mb-5 flex items-center gap-2'>
        <Icon className='size-4 text-primary' />
        <h2 className='font-semibold'>{title}</h2>
      </div>
      <div className='grid grid-cols-4 gap-2'>
        {stages.map(([label, value], index) => (
          <div key={label} className='relative min-w-0'>
            <div className='rounded-xl bg-muted/50 p-3 text-center'>
              <p className='text-lg font-bold'>{value}</p>
              <p className='truncate text-[11px] text-muted-foreground'>
                {label}
              </p>
            </div>
            {index < stages.length - 1 && (
              <span className='absolute top-1/2 -right-2 z-10 hidden -translate-y-1/2 text-muted-foreground sm:block'>
                →
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function DataTable({
  title,
  columns,
  rows,
}: {
  title: string
  columns: string[]
  rows: string[][]
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='mb-4'>
        <h2 className='font-semibold'>{title}</h2>
        <p className='text-xs text-muted-foreground'>Preview data</p>
      </div>
      <div className='overflow-x-auto'>
        <table className='w-full text-sm'>
          <thead>
            <tr className='border-b text-left text-xs text-muted-foreground'>
              {columns.map((column) => (
                <th key={column} className='pr-4 pb-3 font-medium'>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className='border-b last:border-0'>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className='py-3 pr-4'>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
