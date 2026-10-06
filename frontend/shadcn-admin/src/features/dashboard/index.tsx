import { useEffect, useState } from 'react'
import {
  ArrowUpRight,
  Pill,
  Receipt,
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
  sales: {
    today: number
    by_category: { category: string; lines: number; units: number; revenue: number }[]
  }
  revenue: { month: number }
  original_vs_generic: { type: string; lines: number; revenue: number }[]
  top_products: { id: number; name: string; units: number; revenue: number; stock: number }[]
  patient_purchases: { patient_id: number; patient_name: string; lines: number; packs: number; revenue: number }[]
  orders: { month: number; completed_month: number }
  prescriptions: { month: number }
  inventory: {
    retail_value: number
    low_stock: number
    expired: number
    critical_expiry: number
    warning_expiry: number
    extended_expiry: number
  }
}

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
            KPI live · synthetic operational data
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
            <DonutCard
              title='Sales by category'
              total={formatCurrency(summary?.sales.by_category.reduce((sum, item) => sum + item.revenue, 0) ?? 0)}
              items={toPercentItems(summary?.sales.by_category.map((item) => [item.category, item.revenue] as [string, number]) ?? [])}
            />
            <DonutCard
              title='Original vs Generic'
              total={formatCurrency(summary?.original_vs_generic.reduce((sum, item) => sum + item.revenue, 0) ?? 0)}
              items={toPercentItems(summary?.original_vs_generic.map((item) => [item.type, item.revenue] as [string, number]) ?? [])}
            />
            <DonutCard
              title='Expiry control'
              total={String((summary?.inventory.expired ?? 0) + (summary?.inventory.critical_expiry ?? 0) + (summary?.inventory.warning_expiry ?? 0) + (summary?.inventory.extended_expiry ?? 0))}
              items={toPercentItems([
                ['Expired', summary?.inventory.expired ?? 0],
                ['≤ 3 months', summary?.inventory.critical_expiry ?? 0],
                ['≤ 9 months', summary?.inventory.warning_expiry ?? 0],
                ['≤ 12 months', summary?.inventory.extended_expiry ?? 0],
              ])}
            />
          </section>

          <section className='grid gap-4 xl:grid-cols-2'>
            <DataTable
              title='Top Products'
              columns={['Product', 'Units', 'Revenue', 'Stock']}
              rows={(summary?.top_products ?? []).map((item) => [
                item.name,
                item.units.toLocaleString(),
                formatCurrency(item.revenue),
                item.stock.toLocaleString(),
              ])}
            />
            <DataTable
              title='Patient Purchases'
              columns={['Patient', 'Lines', 'Packs', 'Revenue']}
              rows={(summary?.patient_purchases ?? []).slice(0, 10).map((item) => [
                item.patient_name,
                item.lines.toLocaleString(),
                item.packs.toLocaleString(),
                formatCurrency(item.revenue),
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

function formatCurrency(value: number) {
  return value.toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  })
}

function toPercentItems(items: [string, number][]): [string, number][] {
  const total = items.reduce((sum, [, value]) => sum + value, 0)
  if (!total) return []
  return items.map(([label, value]) => [label, Math.round((value / total) * 100)] as [string, number])
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
