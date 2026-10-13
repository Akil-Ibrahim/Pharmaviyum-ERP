import { useCallback, useEffect, useRef, useState } from 'react'
import './dashboard.css'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  Boxes,
  Clock3,
  ClipboardList,
  FileText,
  Pill,
  PackageSearch,
  Receipt,
  RefreshCw,
  Send,
  Sparkles,
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
  patient_purchases: { patient_id: number; patient_name: string; lines: number; packs: number; revenue: number }[]
  patient_medications: {
    patient_id: number
    patient_name: string
    condition: string | null
    medications: {
      purchase_id: number
      product_id: number
      name: string
      dosage: string | null
      form: string | null
      pack_size: number
      packs: number
      amount: number
      prescription_required: boolean
      type: 'Generic' | 'Original' | 'Unclassified'
      expiry_date: string | null
    }[]
  }[]
  reorder_attention: { id: number; name: string; available_packs: number; reorder_level: number; packs_30d: number; days_on_hand: number | null; stock_value: number }[]
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
    days_on_hand: number | null
    demand_30d_packs: number
    expired_value: number
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
  const [loadErrorMessage, setLoadErrorMessage] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [aiPharmacies, setAiPharmacies] = useState<{ id: number; name: string }[]>([])
  const [aiContextLoading, setAiContextLoading] = useState(true)
  const [aiPharmacyId, setAiPharmacyId] = useState<number | undefined>()
  const [aiQuery, setAiQuery] = useState('')
  const [aiAnswer, setAiAnswer] = useState('')
  const [aiError, setAiError] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const requestInFlight = useRef(false)

  const loadSummary = useCallback(() => {
    if (requestInFlight.current) return
    requestInFlight.current = true
    setIsRefreshing(true)
    apiFetch<DashboardSummary>('/api/v1/dashboard/summary')
      .then((data) => {
        setSummary(data)
        setLoadError(false)
        setLoadErrorMessage(null)
        setLastUpdated(new Date())
      })
      .catch((error: unknown) => {
        setLoadError(true)
        setLoadErrorMessage(
          error instanceof Error && error.message.trim()
            ? error.message.slice(0, 160)
            : 'Unable to reach the dashboard API. Check your connection and session.'
        )
      })
      .finally(() => {
        requestInFlight.current = false
        setIsRefreshing(false)
      })
  }, [])

  useEffect(() => {
    const initialLoad = window.setTimeout(loadSummary, 0)
    const interval = window.setInterval(loadSummary, 30_000)
    return () => {
      window.clearTimeout(initialLoad)
      window.clearInterval(interval)
    }
  }, [loadSummary])

  useEffect(() => {
    let cancelled = false
    apiFetch<{ pharmacies: { id: number; name: string }[] }>('/api/v1/ai/context')
      .then(({ pharmacies }) => {
        if (cancelled) return
        setAiPharmacies(pharmacies)
        setAiPharmacyId((current) => current ?? pharmacies[0]?.id)
        setAiContextLoading(false)
        setAiError(null)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        setAiContextLoading(false)
        setAiError(
          error instanceof Error && error.message.trim()
            ? error.message.slice(0, 160)
            : 'Mortarium context is currently unavailable.'
        )
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function askMortarium(prompt: string) {
    if (!prompt.trim() || !aiPharmacyId || aiLoading) return
    setAiLoading(true)
    setAiError(null)
    try {
      const result = await apiFetch<{ answer: string }>('/api/v1/ai/query', {
        method: 'POST',
        body: JSON.stringify({
          query: prompt.trim(),
          pharmacy_id: aiPharmacyId,
          language: 'en',
          country: 'VN',
        }),
      })
      setAiAnswer(result.answer)
      setAiQuery('')
    } catch (error) {
      setAiError(
        error instanceof Error && error.message.trim()
          ? error.message.slice(0, 200)
          : 'Mortarium could not complete the request. Please retry.'
      )
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <>
      <Header>
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='pharmaviyum-dashboard'>
          <div className='pharmacy-dashboard-hero mb-5 flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5'>
            <div className='max-w-2xl'>
              <div className='mb-2 inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.12em] text-primary'>
                <Activity className='size-3.5' />
                Operations / Overview
              </div>
              <h1 className='text-2xl font-bold tracking-tight sm:text-3xl'>
                Pharmacy operations
              </h1>
              <p className='mt-1.5 max-w-xl text-sm leading-5 text-muted-foreground'>
                Sales, stock availability, expiry risk and procurement priorities across your pharmacy.
              </p>
            </div>
            <div className='flex flex-wrap items-center gap-3'>
              <span className='inline-flex items-center gap-2 rounded-md border bg-background/80 px-3 py-2 text-xs font-medium text-muted-foreground'>
                <span className={loadError ? 'size-2 rounded-full bg-destructive' : summary ? 'size-2 rounded-full bg-emerald-500' : 'size-2 rounded-full bg-amber-500'} />
                {loadError ? 'Connection issue' : isRefreshing ? 'Syncing ERP data' : summary ? 'ERP connected' : 'Waiting for data'}
              </span>
              <button
                type='button'
                onClick={loadSummary}
                disabled={isRefreshing}
                className='inline-flex items-center gap-2 rounded-md bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:cursor-wait disabled:opacity-60'
              >
                <RefreshCw className={isRefreshing ? 'size-4 animate-spin' : 'size-4'} />
                Refresh data
              </button>
            </div>
            <p className='text-xs text-muted-foreground sm:absolute sm:bottom-2 sm:left-5'>
              {lastUpdated
                ? 'Last successful sync ' + lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'Operational indicators load from your ERP records'}
            </p>
          </div>

          {loadError && (
            <div className='flex flex-col gap-3 rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between'>
              <div>
                <p className='font-semibold text-destructive'>
                  {summary ? 'Showing the last successfully loaded data' : 'Dashboard data could not be loaded'}
                </p>
                <p className='mt-1 text-muted-foreground'>
                  {loadErrorMessage ?? 'Check the API connection or your session, then retry.'} Data is not being replaced with demo values.
                </p>
              </div>
              <button
                type='button'
                onClick={loadSummary}
                disabled={isRefreshing}
                className='inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border bg-background px-3 py-2 text-xs font-semibold transition hover:bg-muted disabled:opacity-60'
              >
                <RefreshCw className={isRefreshing ? 'size-3.5 animate-spin' : 'size-3.5'} />
                Retry connection
              </button>
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
                label='Revenue this month'
                value={summary ? formatAmount(summary.revenue.month) : '—'}
                detail={summary ? 'Realized revenue · current month' : 'Awaiting API data'}
                icon={Pill}
              />
              <KpiCard
                label='Stockouts'
                value={summary ? summary.attention.stockout_items.toLocaleString() : '—'}
                detail={summary ? 'Products with no available stock' : 'Awaiting API data'}
                icon={Boxes}
              />
            </section>

            <section aria-label='Operational priorities' className='pharmacy-priority-panel rounded-xl border bg-card'>
              <div className='flex flex-wrap items-start justify-between gap-3 border-b px-4 py-3 sm:px-5'>
                <div className='flex items-start gap-3'>
                  <div className='rounded-lg bg-primary/10 p-2 text-primary'><ClipboardList className='size-5' /></div>
                  <div>
                    <h2 className='font-semibold'>Today’s priority queue</h2>
                    <p className='mt-0.5 text-xs text-muted-foreground'>Actionable exceptions from current pharmacy records</p>
                  </div>
                </div>
                <span className='rounded-md border bg-muted/30 px-2.5 py-1 text-[11px] font-medium text-muted-foreground'>Live operational data</span>
              </div>
              <div className='grid divide-y sm:grid-cols-3 sm:divide-x sm:divide-y-0'>
                <PriorityItem
                  icon={PackageSearch}
                  tone='warning'
                  label='Replenishment'
                  value={summary ? summary.inventory.low_stock.toLocaleString() : '—'}
                  detail={summary ? `${summary.reorder_attention.length} products need review` : 'Waiting for inventory data'}
                  href='#procurement-attention'
                  action='Review stock'
                />
                <PriorityItem
                  icon={Clock3}
                  tone='critical'
                  label='Expiry exposure'
                  value={summary ? (summary.inventory.expiry_red + summary.inventory.expiry_yellow).toLocaleString() : '—'}
                  detail={summary ? `${summary.inventory.expired} expired records · ${summary.inventory.critical_expiry} critical` : 'Waiting for batch data'}
                  href='#expiry-control'
                  action='Review expiry'
                />
                <PriorityItem
                  icon={AlertTriangle}
                  tone='warning'
                  label='Slow-moving stock'
                  value={summary ? summary.attention.slow_moving_items.toLocaleString() : '—'}
                  detail={summary ? `${formatAmount(summary.attention.slow_moving_stock_value)} tied up in stock` : 'Waiting for stock movement data'}
                  href='#slow-moving-stock'
                  action='Inspect products'
                />
              </div>
            </section>

            <section id='expiry-control' className='grid gap-4 xl:grid-cols-3'>
              <DonutCard
                title='Sales mix'
                total={formatAmount(summary?.sales.by_category.reduce((sum, item) => sum + item.revenue, 0) ?? 0)}
                items={toPercentItems(summary?.sales.by_category.map((item) => [item.category, item.revenue] as [string, number]) ?? [])}
              />
              <DonutCard
                title='Expiry control'
                total={String(summary?.inventory.expiry_tracked ?? 0)}
                items={toPercentItems([
                  ['Red · expired / ≤ 3 months', summary?.inventory.expiry_red ?? 0],
                  ['Yellow · > 3–12 months', summary?.inventory.expiry_yellow ?? 0],
                  ['Green · > 12 months', summary?.inventory.expiry_green ?? 0],
                ])}
              />
              <DonutCard
                title='Stock availability'
                total={String(summary?.inventory.items ?? 0)}
                items={toPercentItems([
                  ['Healthy stock', Math.max(0, (summary?.inventory.items ?? 0) - (summary?.inventory.low_stock ?? 0))],
                  ['Low stock', Math.max(0, (summary?.inventory.low_stock ?? 0) - (summary?.attention.stockout_items ?? 0))],
                  ['Stockout', summary?.attention.stockout_items ?? 0],
                ])}
              />
            </section>

            <section>
              <div className='mb-3'>
                <h2 className='font-semibold'>Operational Health</h2>
                <p className='text-xs text-muted-foreground'>At-a-glance signals for daily pharmacy management.</p>
              </div>
              <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
                <CircularMetricCard
                  label='Order completion'
                  value={ratio(summary?.orders.completed_month ?? 0, summary?.orders.month ?? 0)}
                  detail='Completed / orders this month'
                />
                <CircularMetricCard
                  label='Availability health'
                  value={ratio(
                    Math.max(0, (summary?.inventory.items ?? 0) - (summary?.inventory.low_stock ?? 0)),
                    summary?.inventory.items ?? 0
                  )}
                  detail='Inventory records above reorder level'
                />
                <CircularMetricCard
                  label='Expiry coverage'
                  value={ratio(summary?.inventory.expiry_green ?? 0, summary?.inventory.expiry_tracked ?? 0)}
                  detail='Tracked records with > 12 months remaining'
                />
                <CircularMetricCard
                  label='Rx share'
                  value={ratio(
                    summary?.sales.by_category.find((item) => item.category === 'Rx')?.revenue ?? 0,
                    summary?.sales.by_category.reduce((sum, item) => sum + item.revenue, 0) ?? 0
                  )}
                  detail='Prescription sales share'
                />
              </div>
            </section>

            <section className='grid gap-4 xl:grid-cols-4'>
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
              <PipelineCard
                title='Patient activity'
                icon={Activity}
                stages={[
                  ['Active patients', summary?.patients.active ?? 0],
                  ['Recent patients', summary?.patient_medications.length ?? 0],
                  ['Medication lines', summary?.patient_medications.reduce((total, patient) => total + patient.medications.length, 0) ?? 0],
                ]}
              />
            </section>

            <section>
              <div className='mb-3'>
                <h2 className='font-semibold'>Inventory Control</h2>
                <p className='text-xs text-muted-foreground'>Runway and stock exposure based on realized dispensing.</p>
              </div>
              <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
                <OperationalMetric
                  label='Days on hand'
                  value={summary?.inventory.days_on_hand == null ? '—' : summary.inventory.days_on_hand + 'd'}
                  detail={summary ? 'Available stock ÷ 30-day pack demand' : 'Awaiting API data'}
                />
                <OperationalMetric
                  label='30-day demand'
                  value={summary ? summary.inventory.demand_30d_packs.toLocaleString() : '—'}
                  detail='Dispensed packs in the last 30 days'
                />
                <OperationalMetric
                  label='Expired stock value'
                  value={summary ? formatAmount(summary.inventory.expired_value) : '—'}
                  detail='Available stock already past expiry'
                />
                <OperationalMetric
                  label='Low-stock products'
                  value={summary ? summary.inventory.low_stock.toLocaleString() : '—'}
                  detail='At or below configured reorder level'
                />
              </div>
            </section>

            <section>
              <div id='inventory-attention' className='mb-3'>
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
              <div id='slow-moving-stock' className='mt-4 rounded-2xl border bg-card p-5 shadow-sm'>
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
              <div id='procurement-attention' className='mb-3'>
                <h2 className='font-semibold'>Procurement Attention</h2>
                <p className='text-xs text-muted-foreground'>Products at or below their configured reorder level, prioritized by available stock.</p>
              </div>
              <div className='rounded-2xl border bg-card p-5 shadow-sm'>
                <div className='space-y-2'>
                  {(summary?.reorder_attention ?? []).map((item) => (
                    <div key={item.id} className='flex flex-wrap items-center gap-3 rounded-xl bg-muted/30 p-3'>
                      <div className='min-w-0 flex-1'>
                        <p className='truncate text-sm font-medium'>{item.name}</p>
                        <p className='text-xs text-muted-foreground'>{item.available_packs} packs available · reorder level {item.reorder_level} units · {item.packs_30d} packs / 30d</p>
                      </div>
                      <div className='text-right'>
                        <p className='text-sm font-semibold'>{item.days_on_hand == null ? 'No demand' : item.days_on_hand + 'd'}</p>
                        <p className='text-[11px] text-muted-foreground'>{formatAmount(item.stock_value)} stock value</p>
                      </div>
                    </div>
                  ))}
                  {summary && summary.reorder_attention.length === 0 && (
                    <p className='py-4 text-center text-xs text-muted-foreground'>No products currently require procurement attention.</p>
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

            <section>
              <div className='mb-3'>
                <h2 className='font-semibold'>Patient Overview</h2>
                <p className='text-xs text-muted-foreground'>20 patients with recent dispensing activity, their key metrics, conditions, and medications.</p>
              </div>
              <PatientOverview summary={summary} />
            </section>

            <section className='overflow-hidden rounded-2xl border bg-card shadow-sm'>
              <div className='flex flex-col gap-4 border-b bg-gradient-to-r from-primary/[0.07] via-card to-card p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5'>
                <div className='flex items-start gap-3'>
                  <div className='rounded-xl border border-primary/15 bg-primary/10 p-2.5 text-primary'>
                    <Bot className='size-5' />
                  </div>
                  <div>
                    <div className='flex flex-wrap items-center gap-2'>
                      <h2 className='font-semibold'>Mortarium AI</h2>
                      <span className='inline-flex items-center gap-1 rounded-full border bg-background/80 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground'>
                        <Sparkles className='size-3' /> Decision support
                      </span>
                    </div>
                    <p className='mt-1 max-w-2xl text-sm leading-5 text-muted-foreground'>
                      Ask questions about stock, expiry exposure, sales and dispensing activity. Answers come from the existing authenticated Mortarium service.
                    </p>
                  </div>
                </div>
                <label className='flex min-w-0 flex-col gap-1 text-xs font-medium text-muted-foreground sm:w-64'>
                  Pharmacy context
                  <select
                    value={aiPharmacyId ?? ''}
                    onChange={(event) => {
                      setAiPharmacyId(event.target.value ? Number(event.target.value) : undefined)
                      setAiAnswer('')
                      setAiError(null)
                    }}
                    disabled={aiPharmacies.length === 0 || aiLoading}
                    className='h-9 w-full rounded-md border bg-background px-2.5 text-sm font-normal text-foreground disabled:opacity-60'
                  >
                    {aiPharmacies.length === 0 && (
                      <option value=''>
                        {aiContextLoading ? 'Loading authorized pharmacies…' : 'No authorized pharmacy available'}
                      </option>
                    )}
                    {aiPharmacies.map((pharmacy) => (
                      <option key={pharmacy.id} value={pharmacy.id}>{pharmacy.name}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className='grid gap-4 p-4 sm:p-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(260px,0.75fr)]'>
                <div className='min-w-0'>
                  <form
                    className='flex gap-2'
                    onSubmit={(event) => {
                      event.preventDefault()
                      void askMortarium(aiQuery)
                    }}
                  >
                    <input
                      value={aiQuery}
                      onChange={(event) => setAiQuery(event.target.value)}
                      placeholder='Ask about inventory, sales or expiry…'
                      aria-label='Ask Mortarium AI'
                      className='min-w-0 flex-1 rounded-lg border bg-background px-3 py-2.5 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-primary/40'
                    />
                    <button
                      type='submit'
                      disabled={!aiPharmacyId || aiLoading || !aiQuery.trim()}
                      className='inline-flex shrink-0 items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50'
                    >
                      {aiLoading ? <RefreshCw className='size-4 animate-spin' /> : <Send className='size-4' />}
                      <span className='hidden sm:inline'>{aiLoading ? 'Analyzing' : 'Ask AI'}</span>
                    </button>
                  </form>

                  {aiError && (
                    <p role='alert' className='mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2 text-xs leading-5 text-destructive'>
                      {aiError}
                    </p>
                  )}

                  {aiLoading && (
                    <div className='mt-4 flex items-center gap-2 text-sm text-muted-foreground' role='status'>
                      <RefreshCw className='size-4 animate-spin' /> Mortarium is analyzing the request…
                    </div>
                  )}

                  {aiAnswer && !aiLoading && (
                    <div className='mt-4 rounded-xl border bg-muted/20 p-4'>
                      <div className='mb-2 flex items-center gap-2 text-xs font-semibold text-primary'>
                        <Bot className='size-4' /> Mortarium response
                      </div>
                      <p className='whitespace-pre-wrap text-sm leading-6'>{aiAnswer}</p>
                    </div>
                  )}

                  {!aiAnswer && !aiError && !aiLoading && (
                    <p className='mt-3 text-xs leading-5 text-muted-foreground'>
                      Recommendations are generated on request. No AI forecasts or recommendations are fabricated for this dashboard.
                    </p>
                  )}
                </div>

                <div className='grid content-start gap-2 sm:grid-cols-2 lg:grid-cols-1'>
                  <p className='mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground sm:col-span-2 lg:col-span-1'>
                    Suggested questions
                  </p>
                  {[
                    'Which products need replenishment first?',
                    'Which batches have the highest expiry risk?',
                    'Summarize this month’s realized sales.',
                    'What stock is moving slowly?',
                  ].map((prompt) => (
                    <button
                      key={prompt}
                      type='button'
                      onClick={() => void askMortarium(prompt)}
                      disabled={!aiPharmacyId || aiLoading}
                      className='flex items-center justify-between gap-3 rounded-lg border bg-background px-3 py-2.5 text-left text-xs leading-5 transition hover:border-primary/30 hover:bg-primary/[0.03] disabled:cursor-not-allowed disabled:opacity-50'
                    >
                      <span>{prompt}</span>
                      <ArrowUpRight className='size-3.5 shrink-0 text-muted-foreground' />
                    </button>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </div>
      </Main>
    </>
  )
}

function PriorityItem({
  icon: Icon,
  tone,
  label,
  value,
  detail,
  href,
  action,
}: {
  icon: LucideIcon
  tone: 'critical' | 'warning'
  label: string
  value: string
  detail: string
  href: string
  action: string
}) {
  return (
    <div className='min-w-0 p-4 sm:p-5'>
      <div className='flex items-center gap-2'>
        <Icon className={tone === 'critical' ? 'size-4 text-red-600 dark:text-red-400' : 'size-4 text-amber-600 dark:text-amber-400'} />
        <span className='text-xs font-semibold uppercase tracking-[0.06em] text-muted-foreground'>{label}</span>
      </div>
      <p className='mt-3 text-3xl font-bold tracking-tight tabular-nums'>{value}</p>
      <p className='mt-1 min-h-8 text-xs leading-5 text-muted-foreground'>{detail}</p>
      <a href={href} className='mt-3 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline'>
        {action}<ArrowUpRight className='size-3.5' aria-hidden='true' />
      </a>
    </div>
  )
}

function PatientOverview({ summary }: { summary: DashboardSummary | null }) {
  const metrics = new Map((summary?.patient_purchases ?? []).map((item) => [item.patient_id, item]))
  const patients = summary?.patient_medications ?? []

  if (!summary) {
    return <div className='rounded-2xl border bg-card p-5 text-sm text-muted-foreground'>Awaiting patient data…</div>
  }

  if (patients.length === 0) {
    return <div className='rounded-2xl border bg-card p-5 text-sm text-muted-foreground'>No patient dispensing data available.</div>
  }

  return (
    <div className='rounded-2xl border bg-card shadow-sm'>
      <div className='overflow-x-auto'>
        <table className='w-full min-w-[980px] text-sm'>
          <thead>
            <tr className='border-b text-left text-xs text-muted-foreground'>
              <th className='px-5 py-3 font-medium'>Patient</th>
              <th className='px-4 py-3 font-medium'>Condition</th>
              <th className='px-4 py-3 font-medium'>Dispensing</th>
              <th className='px-4 py-3 font-medium'>Packs</th>
              <th className='px-4 py-3 font-medium'>Revenue</th>
              <th className='px-5 py-3 font-medium'>Medications</th>
            </tr>
          </thead>
          <tbody>
            {patients.slice(0, 20).map((patient) => {
              const metric = metrics.get(patient.patient_id)
              const medicationCount = patient.medications.length
              const rxCount = patient.medications.filter((medication) => medication.prescription_required).length
              return (
                <tr key={patient.patient_id} className='border-b align-top last:border-0'>
                  <td className='px-5 py-4'>
                    <div className='font-medium'>{patient.patient_name}</div>
                    <div className='text-xs text-muted-foreground'>#{patient.patient_id}</div>
                  </td>
                  <td className='px-4 py-4'>
                    <span className='rounded-full border bg-muted/40 px-2 py-1 text-xs'>
                      {patient.condition ?? 'Not recorded'}
                    </span>
                  </td>
                  <td className='px-4 py-4 whitespace-nowrap'>
                    <div className='font-medium'>{metric?.lines ?? medicationCount} lines</div>
                    <div className='text-xs text-muted-foreground'>{rxCount} Rx · {medicationCount - rxCount} OTC</div>
                  </td>
                  <td className='px-4 py-4 font-medium whitespace-nowrap'>{metric?.packs ?? 0}</td>
                  <td className='px-4 py-4 font-medium whitespace-nowrap'>{formatAmount(metric?.revenue ?? 0)}</td>
                  <td className='px-5 py-4'>
                    <details className='group'>
                      <summary className='cursor-pointer list-none font-medium text-primary'>
                        <span className='group-open:hidden'>{medicationCount} medications · view details</span>
                        <span className='hidden group-open:inline'>Hide medication details</span>
                      </summary>
                      <div className='mt-3 space-y-2'>
                        {patient.medications.map((medication) => (
                          <div key={medication.purchase_id} className='rounded-xl bg-muted/30 p-3'>
                            <div className='flex flex-wrap items-start justify-between gap-2'>
                              <div className='min-w-0'>
                                <div className='font-medium'>{medication.name}</div>
                                <div className='text-xs text-muted-foreground'>
                                  {[medication.dosage, medication.form].filter(Boolean).join(' · ') || 'Dosage not recorded'} · pack {medication.pack_size}
                                </div>
                              </div>
                              <span className='rounded-full border px-2 py-0.5 text-[10px]'>
                                {medication.prescription_required ? 'Rx' : 'OTC'} · {medication.type}
                              </span>
                            </div>
                            <div className='mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground'>
                              <span>{medication.packs} packs</span>
                              <span>{formatAmount(medication.amount)} revenue</span>
                              <span>{medication.expiry_date ? 'Expiry ' + formatExpiry(medication.expiry_date) : 'Expiry not recorded'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function formatExpiry(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, { month: 'short', year: 'numeric' }).format(date)
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

function OperationalMetric({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <div className='rounded-2xl border bg-card p-5 shadow-sm'>
      <p className='text-sm text-muted-foreground'>{label}</p>
      <p className='mt-2 text-2xl font-bold tracking-tight'>{value}</p>
      <p className='mt-1 text-xs text-muted-foreground'>{detail}</p>
    </div>
  )
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
      <div className='grid grid-cols-2 gap-2 sm:grid-cols-3'>
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
