import { useCallback, useEffect, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  Boxes,
  FileText,
  Pill,
  Receipt,
  Users,
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
  sales: {
    today: number
    by_category: { category: string; lines: number; packs: number; revenue: number }[]
  }
  revenue: { month: number }
  top_products: { id: number; name: string; packs: number; revenue: number; stock: number }[]
  orders: { month: number; completed_month: number }
  prescriptions: { month: number }
  attention: {
    stockout_items: number
    near_expiry_value: number
    slow_moving_items: number
    slow_moving_stock_value: number
    slow_moving: { id: number; name: string; packs_90d: number; stock: number; stock_value: number }[]
  }
  inventory: {
    retail_value: number
    items: number
    low_stock: number
    expired: number
    critical_expiry: number
    warning_expiry: number
    extended_expiry: number
    expiry_tracked: number
    expiry_red: number
    expiry_yellow: number
    expiry_green: number
  }
}

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const loadSummary = useCallback(() => {
    setIsRefreshing(true)
    apiFetch<DashboardSummary>('/api/v1/dashboard/summary')
      .then((data) => {
        setSummary(data)
        setLoadError(false)
      })
      .catch(() => setLoadError(true))
      .finally(() => setIsRefreshing(false))
  }, [])

  useEffect(() => {
    const initialLoad = window.setTimeout(loadSummary, 0)
    const interval = window.setInterval(loadSummary, 30_000)
    return () => {
      window.clearTimeout(initialLoad)
      window.clearInterval(interval)
    }
  }, [loadSummary])

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
            {isRefreshing ? 'Refreshing…' : 'KPI live'} · synthetic operational data
          </span>
        </div>

        {loadError && (
          <div className='rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive'>
            Dashboard data is temporarily unavailable. Showing the last loaded values; retrying automatically.
          </div>
        )}

        <div className='space-y-6'>
          <section className='grid gap-4 md:grid-cols-3'>
            <KpiCard
              label='Sales today'
              value={summary ? formatAmount(summary.sales.today) : '—'}
              detail={summary ? 'Realized dispensing / POS sales' : 'Awaiting API data'}
              icon={Receipt}
            />
            <KpiCard
              label='Active patients'
              value={summary ? summary.patients.active.toLocaleString() : '—'}
              detail={summary ? 'Current patient profiles' : 'Awaiting API data'}
              icon={Users}
            />
            <KpiCard
              label='Stockouts'
              value={summary ? summary.attention.stockout_items.toLocaleString() : '—'}
              detail={summary ? 'Products with no available stock' : 'Awaiting API data'}
              icon={Boxes}
            />
          </section>

          <section className='grid gap-4 xl:grid-cols-3'>
            <PipelineCard
              title='Dispensing / POS'
              icon={Receipt}
              stages={[
                ['Orders', summary?.orders.month ?? 0],
                ['Completed', summary?.orders.completed_month ?? 0],
                ['Sales today', summary?.sales.today ?? 0, true],
              ]}
            />
            <PipelineCard
              title='Prescriptions'
              icon={FileText}
              stages={[
                ['Rx this month', summary?.prescriptions.month ?? 0],
                ['Orders', summary?.orders.month ?? 0],
                ['Completion', ratio(summary?.orders.completed_month ?? 0, summary?.orders.month ?? 0)],
              ]}
            />
            <PipelineCard
              title='Inventory control'
              icon={Boxes}
              stages={[
                ['Stock value', summary?.inventory.retail_value ?? 0, true],
                ['Low stock', summary?.inventory.low_stock ?? 0],
                ['Expiry risk', (summary?.inventory.expiry_red ?? 0) + (summary?.inventory.expiry_yellow ?? 0)],
              ]}
            />
          </section>

          <section>
            <div className='mb-3'>
              <h2 className='font-semibold'>Inventory Attention</h2>
              <p className='text-xs text-muted-foreground'>Exceptions that can affect availability, working capital, or expiry losses.</p>
            </div>
            <div className='grid gap-4 xl:grid-cols-3'>
              <AttentionCard
                title='Stockouts'
                value={summary?.attention.stockout_items ?? 0}
                detail='Products with zero available stock'
                tone='critical'
              />
              <AttentionCard
                title='Near-expiry value'
                value={summary?.attention.near_expiry_value ?? 0}
                detail='Stock value expiring within 12 months'
                tone='warning'
                amount
              />
              <AttentionCard
                title='Slow-moving stock'
                value={summary?.attention.slow_moving_stock_value ?? 0}
                detail={summary ? `${summary.attention.slow_moving_items} products with no sales in 90 days` : 'Awaiting API data'}
                tone='warning'
                amount
              />
            </div>
            <div className='mt-4 rounded-2xl border bg-card p-5 shadow-sm'>
              <div className='mb-4 flex items-center justify-between gap-3'>
                <div>
                  <h3 className='font-semibold'>Slow-moving products</h3>
                  <p className='text-xs text-muted-foreground'>Highest inventory value with no sales in the last 90 days.</p>
                </div>
                <span className='rounded-full border bg-muted/40 px-2 py-1 text-[11px] text-muted-foreground'>90 days</span>
              </div>
              <div className='space-y-2'>
                {(summary?.attention.slow_moving ?? []).map((item) => (
                  <div key={item.id} className='flex items-center gap-3 rounded-xl bg-muted/30 p-3'>
                    <div className='min-w-0 flex-1'>
                      <p className='truncate text-sm font-medium'>{item.name}</p>
                      <p className='text-xs text-muted-foreground'>{item.stock.toLocaleString()} units · {item.packs_90d} packs sold</p>
                    </div>
                    <span className='text-sm font-semibold'>{formatAmount(item.stock_value)}</span>
                  </div>
                ))}
                {summary && summary.attention.slow_moving.length === 0 && (
                  <p className='py-4 text-center text-xs text-muted-foreground'>No slow-moving stock detected.</p>
                )}
              </div>
            </div>
          </section>

          <section>
            <DataTable
              title='Top dispensed products'
              columns={['Product', 'Packs', 'Revenue', 'Available stock']}
              rows={(summary?.top_products ?? []).map((item) => [
                item.name,
                item.packs.toLocaleString(),
                formatAmount(item.revenue),
                item.stock.toLocaleString(),
              ])}
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
                  Mortarium AI metrics remain isolated from operational KPI calculations.
                  The dashboard uses ERP records for business metrics and keeps AI telemetry separate.
                </p>
              </div>
            </div>
          </section>
        </div>
      </Main>
    </>
  )
}

function formatAmount(value: number) {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: 0,
  })
}

function toPercentItems(items: [string, number][]): [string, number][] {
  const total = items.reduce((sum, [, value]) => sum + value, 0)
  if (!total) return []
  return items.map(([label, value]) => [label, Math.round((value / total) * 100)] as [string, number])
}

function ratio(numerator: number, denominator: number) {
  if (!denominator) return 0
  return Math.min(100, Math.round((numerator / denominator) * 100))
}

function CircularMetricCard({
  label,
  value,
  detail,
}: {
  label: string
  value: number
  detail: string
}) {
  const angle = Math.max(0, Math.min(100, value)) * 3.6
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='flex items-center gap-4'>
        <div
          className='relative grid size-24 shrink-0 place-items-center rounded-full'
          style={{
            background: `conic-gradient(hsl(var(--primary)) ${angle}deg, hsl(var(--muted)) ${angle}deg)`,
          }}
        >
          <div className='grid size-18 place-items-center rounded-full bg-card'>
            <span className='text-xl font-bold'>{value}%</span>
          </div>
        </div>
        <div className='min-w-0'>
          <p className='font-semibold'>{label}</p>
          <p className='mt-1 text-xs leading-5 text-muted-foreground'>{detail}</p>
        </div>
      </div>
    </div>
  )
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
        <p className='text-xs text-muted-foreground'>Live ERP aggregation</p>
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
          {items.length === 0 && <span className='text-xs text-muted-foreground'>No operational data</span>}
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

function AttentionCard({
  title,
  value,
  detail,
  tone,
  amount = false,
}: {
  title: string
  value: number
  detail: string
  tone: 'critical' | 'warning'
  amount?: boolean
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='flex items-center justify-between'>
        <span className='text-sm font-medium'>{title}</span>
        <span className={tone === 'critical' ? 'rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-600 dark:text-red-400' : 'rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400'}>
          Attention
        </span>
      </div>
      <p className='mt-4 text-3xl font-bold tracking-tight'>{amount ? formatAmount(value) : value.toLocaleString()}</p>
      <p className='mt-1 text-xs text-muted-foreground'>{detail}</p>
    </div>
  )
}

function LiveStatCard({
  label,
  value,
  detail,
  direction,
  amount = false,
}: {
  label: string
  value: number
  detail: string
  direction: 'up' | 'down'
  amount?: boolean
}) {
  return (
    <div className='rounded-xl border bg-card p-4 shadow-sm'>
      <div className='flex items-center justify-between'>
        <span className='text-sm text-muted-foreground'>{label}</span>
        {direction === 'up' ? (
          <ArrowUpRight className='size-4 text-emerald-600' />
        ) : (
          <ArrowDownRight className='size-4 text-amber-600' />
        )}
      </div>
      <div className='mt-2 text-2xl font-semibold tracking-tight'>
        {amount ? formatAmount(value) : value.toLocaleString()}
      </div>
      <div className='mt-1 text-xs text-muted-foreground'>{detail}</div>
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
  stages: [string, number, boolean?][]
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='mb-5 flex items-center gap-2'>
        <Icon className='size-4 text-primary' />
        <h2 className='font-semibold'>{title}</h2>
      </div>
      <div className='grid grid-cols-2 gap-2 sm:grid-cols-4'>
        {stages.map(([label, value, amount], index) => (
          <div key={label} className='relative min-w-0'>
            <div className='rounded-xl bg-muted/50 p-3 text-center'>
              <p className='text-lg font-bold'>{amount ? formatAmount(value) : value.toLocaleString()}</p>
              <p className='truncate text-[11px] text-muted-foreground'>{label}</p>
            </div>
            {index < stages.length - 1 && (
              <span className='absolute top-1/2 -right-2 z-10 hidden -translate-y-1/2 text-muted-foreground sm:block'>→</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function PatientCohortCard({
  patients,
  details,
}: {
  patients: DashboardSummary['patient_purchases']
  details: DashboardSummary['patient_medications']
}) {
  const totalLines = patients.reduce((sum, patient) => sum + patient.lines, 0)
  const totalPacks = patients.reduce((sum, patient) => sum + patient.packs, 0)
  const totalRevenue = patients.reduce((sum, patient) => sum + patient.revenue, 0)
  const detailByPatient = new Map(details.map((patient) => [patient.patient_id, patient]))

  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <div className='mb-4 flex items-start justify-between gap-3'>
        <div>
          <h2 className='font-semibold'>Patient Purchases</h2>
          <p className='text-xs text-muted-foreground'>
            Patient, condition, medicines, pack size, quantity, expiry and realized amount
          </p>
        </div>
        <span className='rounded-full border bg-muted/40 px-2 py-1 text-[11px] text-muted-foreground'>
          {patients.length} patients
        </span>
      </div>

      <div className='mb-4 grid grid-cols-3 gap-2'>
        <MiniMetric label='Medicines' value={totalLines} />
        <MiniMetric label='Packs' value={totalPacks} />
        <MiniMetric label='Revenue' value={totalRevenue} amount />
      </div>

      <div className='max-h-[620px] overflow-auto pr-1'>
        <div className='space-y-2'>
          {patients.map((patient) => {
            const detail = detailByPatient.get(patient.patient_id)
            return (
              <details key={patient.patient_id} className='group rounded-xl border bg-muted/20'>
                <summary className='flex cursor-pointer list-none items-center gap-3 p-3 [&::-webkit-details-marker]:hidden'>
                  <div className='min-w-0 flex-1'>
                    <div className='flex items-center gap-2'>
                      <span className='truncate text-sm font-medium'>{patient.patient_name}</span>
                      {detail?.condition && (
                        <span className='hidden rounded-full border bg-card px-2 py-0.5 text-[10px] text-muted-foreground sm:inline'>
                          {detail.condition}
                        </span>
                      )}
                    </div>
                    <p className='mt-1 text-[11px] text-muted-foreground'>
                      {patient.lines} medicines · {patient.packs} packs · {formatAmount(patient.revenue)}
                    </p>
                  </div>
                  <span className='text-xs text-muted-foreground transition-transform group-open:rotate-180'>⌄</span>
                </summary>

                {detail && (
                  <div className='border-t px-3 pb-3'>
                    <div className='mt-3 overflow-x-auto'>
                      <table className='w-full min-w-[700px] text-xs'>
                        <thead>
                          <tr className='border-b text-left text-muted-foreground'>
                            <th className='py-2 pr-3 font-medium'>Medicine</th>
                            <th className='py-2 pr-3 font-medium'>Dosage</th>
                            <th className='py-2 pr-3 text-right font-medium'>Pack</th>
                            <th className='py-2 pr-3 text-right font-medium'>Packs</th>
                            <th className='py-2 pr-3 font-medium'>Type</th>
                            <th className='py-2 pr-3 font-medium'>Expiry</th>
                            <th className='py-2 text-right font-medium'>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.medications.map((medication) => (
                            <tr key={medication.purchase_id} className='border-b last:border-0'>
                              <td className='py-2 pr-3 font-medium'>{medication.name}</td>
                              <td className='py-2 pr-3 text-muted-foreground'>
                                {medication.dosage ?? medication.form ?? '—'}
                              </td>
                              <td className='py-2 pr-3 text-right'>{medication.pack_size || '—'}</td>
                              <td className='py-2 pr-3 text-right'>{medication.packs}</td>
                              <td className='py-2 pr-3'>
                                <span className={medication.type === 'Generic' ? 'text-muted-foreground' : medication.type === 'Original' ? 'font-medium text-primary' : 'text-muted-foreground'}>
                                  {medication.type}
                                  {medication.prescription_required ? ' · Rx' : ' · OTC'}
                                </span>
                              </td>
                              <td className='py-2 pr-3 whitespace-nowrap'>
                                <ExpiryBadge expiryDate={medication.expiry_date} />
                              </td>
                              <td className='py-2 text-right font-medium'>{formatAmount(medication.amount)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </details>
            )
          })}
        </div>
        {patients.length === 0 && (
          <p className='py-6 text-center text-xs text-muted-foreground'>
            No patient purchase data
          </p>
        )}
      </div>
    </div>
  )
}

function ExpiryBadge({ expiryDate }: { expiryDate: string | null }) {
  if (!expiryDate) {
    return <span className='text-muted-foreground'>—</span>
  }

  const expiry = new Date(expiryDate)
  if (Number.isNaN(expiry.getTime())) {
    return <span className='text-muted-foreground'>Invalid expiry</span>
  }
  const today = new Date()
  const expiryMonth = new Date(expiry.getFullYear(), expiry.getMonth(), 1)
  const currentMonth = new Date(today.getFullYear(), today.getMonth(), 1)
  const monthsUntilExpiry =
    (expiryMonth.getFullYear() - currentMonth.getFullYear()) * 12 +
    expiryMonth.getMonth() -
    currentMonth.getMonth()

  const state =
    monthsUntilExpiry <= 3
      ? {
          label: monthsUntilExpiry < 0 ? 'Expired' : '≤ 3m',
          className: 'border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400',
        }
      : monthsUntilExpiry <= 12
        ? {
            label: '> 3–12m',
            className: 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400',
          }
        : {
            label: '> 12m',
            className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
          }

  return (
    <div className='flex items-center gap-2'>
      <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium ${state.className}`}>
        {state.label}
      </span>
      <span className='text-muted-foreground'>{formatExpiry(expiryDate)}</span>
    </div>
  )
}

function formatExpiry(value: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

function MiniMetric({
  label,
  value,
  amount = false,
}: {
  label: string
  value: number
  amount?: boolean
}) {
  return (
    <div className='rounded-xl bg-muted/50 p-3'>
      <p className='text-[11px] text-muted-foreground'>{label}</p>
      <p className='mt-1 text-sm font-semibold'>
        {amount ? formatAmount(value) : value.toLocaleString()}
      </p>
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
        <p className='text-xs text-muted-foreground'>Live ERP aggregation</p>
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
