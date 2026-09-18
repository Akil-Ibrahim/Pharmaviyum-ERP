import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { TopNav } from '@/components/layout/top-nav'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Analytics } from './components/analytics'
import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/api-client'

export function Dashboard() {
  const [stats, setStats] = useState<PatientStatistics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<PatientStatistics>('/api/v1/patients/statistics')
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  const loyaltyMembers = stats
    ? Object.entries(stats.by_loyalty_tier)
        .filter(([tier]) => tier.toLowerCase() !== 'standard')
        .reduce((sum, [, count]) => sum + count, 0)
    : 0

  const topCountries = stats
    ? Object.entries(stats.by_country).sort((a, b) => b[1] - a[1]).slice(0, 6)
    : []

  return (
    <>
      <Header>
        <TopNav links={topNav} className='me-auto' />
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>Pharmacy Dashboard</h1>
          <p className='text-muted-foreground'>Live patient, loyalty, revenue, and geographic metrics from the pharmacy database.</p>
        </div>

        {loading ? (
          <div className='rounded-xl border p-6 text-sm text-muted-foreground'>Loading pharmacy statistics...</div>
        ) : (
          <div className='space-y-6'>
            <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
              <MetricCard label='Total patients' value={String(stats?.total ?? 0)} detail='Full patient database' tone='blue' />
              <MetricCard label='Active patients' value={String(stats?.active ?? 0)} detail='Currently active profiles' tone='green' />
              <MetricCard label='Purchase value' value={formatCurrency(stats?.total_purchase_value ?? 0)} detail='Lifetime recorded value' tone='yellow' />
              <MetricCard label='Loyalty members' value={String(loyaltyMembers)} detail='Non-standard loyalty tiers' tone='purple' />
            </div>

            <div className='grid gap-6 lg:grid-cols-2'>
              <section className='rounded-2xl border bg-card p-5 shadow-sm'>
                <div className='mb-4'><h2 className='font-semibold'>Loyalty distribution</h2><p className='text-xs text-muted-foreground'>Active patients by loyalty tier.</p></div>
                <div className='space-y-3'>
                  {Object.entries(stats?.by_loyalty_tier ?? {}).sort((a, b) => b[1] - a[1]).map(([tier, count]) => {
                    const total = stats?.active ?? 1
                    const percent = Math.round((count / Math.max(total, 1)) * 100)
                    return <div key={tier}><div className='mb-1 flex justify-between text-sm'><span>{tier}</span><span className='text-muted-foreground'>{count} · {percent}%</span></div><div className='h-2 rounded-full bg-muted'><div className='h-2 rounded-full bg-primary' style={{ width: percent + '%' }} /></div></div>
                  })}
                </div>
              </section>

              <section className='rounded-2xl border bg-card p-5 shadow-sm'>
                <div className='mb-4'><h2 className='font-semibold'>Patient geography</h2><p className='text-xs text-muted-foreground'>Top active patient countries.</p></div>
                <div className='space-y-2'>
                  {topCountries.map(([country, count]) => <div key={country} className='flex items-center justify-between rounded-lg border p-3'><span className='font-medium'>{country}</span><span className='text-sm text-muted-foreground'>{count} patients</span></div>)}
                  {topCountries.length === 0 && <p className='text-sm text-muted-foreground'>No geographic data recorded.</p>}
                </div>
              </section>
            </div>

            <section className='rounded-2xl border bg-card p-5 shadow-sm'>
              <div className='mb-4'><h2 className='font-semibold'>Pharmacy operational snapshot</h2><p className='text-xs text-muted-foreground'>Static metrics are sourced from persisted patient data; no synthetic dashboard values.</p></div>
              <div className='grid gap-4 sm:grid-cols-3'>
                <Snapshot label='Inactive patients' value={String(stats?.inactive ?? 0)} />
                <Snapshot label='Loyalty tiers' value={String(Object.keys(stats?.by_loyalty_tier ?? {}).length)} />
                <Snapshot label='Countries' value={String(Object.keys(stats?.by_country ?? {}).length)} />
              </div>
            </section>
          </div>
        )}
      </Main>
    </>
  )
}

type PatientStatistics = {
  total: number
  active: number
  inactive: number
  total_purchase_value: number
  by_loyalty_tier: Record<string, number>
  by_country: Record<string, number>
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function MetricCard({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: 'blue' | 'green' | 'yellow' | 'purple' }) {
  const classes = {
    blue: 'border-sky-200 bg-sky-50/80 dark:border-sky-900 dark:bg-sky-950/30',
    green: 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-900 dark:bg-emerald-950/30',
    yellow: 'border-amber-200 bg-amber-50/80 dark:border-amber-900 dark:bg-amber-950/30',
    purple: 'border-purple-200 bg-purple-50/80 dark:border-purple-900 dark:bg-purple-950/30',
  }
  return <div className={'rounded-2xl border p-5 shadow-sm ' + classes[tone]}><p className='text-sm font-medium'>{label}</p><p className='mt-3 text-3xl font-bold tracking-tight'>{value}</p><p className='mt-1 text-xs text-muted-foreground'>{detail}</p></div>
}

function Snapshot({ label, value }: { label: string; value: string }) {
  return <div className='rounded-xl border bg-muted/20 p-4'><p className='text-xs text-muted-foreground'>{label}</p><p className='mt-1 text-2xl font-semibold'>{value}</p></div>
}

const topNav = [
  {
    title: 'Overview',
    href: 'dashboard/overview',
    isActive: true,
    disabled: false,
  },
  {
    title: 'Customers',
    href: 'dashboard/customers',
    isActive: false,
    disabled: true,
  },
  {
    title: 'Products',
    href: 'dashboard/products',
    isActive: false,
    disabled: true,
  },
  {
    title: 'Settings',
    href: 'dashboard/settings',
    isActive: false,
    disabled: true,
  },
]
