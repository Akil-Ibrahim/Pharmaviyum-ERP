import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { apiFetch } from '@/lib/api-client'

type Patient = { id: number; full_name: string; phone: string; email?: string; city?: string; country: string; customer_category: string; loyalty_tier: string; total_purchases: number; visit_count: number; is_active: boolean }
type PatientStatistics = { total: number; active: number; inactive: number; by_loyalty_tier: Record<string, number>; by_country: Record<string, number> }
type PatientDetail = Patient & { loyalty_points: number; conditions: Array<{ condition_name: string; severity: string; status: string; is_chronic: boolean }>; purchases: Array<{ id: number; receipt_number: string; category: string; product_id?: number; product_name?: string; batch_number?: string; expiry_date?: string; quantity: number; dispensed_packs?: number; dispensed_blisters?: number; dispensed_units?: number; unit_price: number; total_amount: number; prescription_required: boolean; purchased_at: string }> }

export const Route = createFileRoute('/_authenticated/patients')({ component: PatientsPage })

function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selected, setSelected] = useState<PatientDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [statistics, setStatistics] = useState<PatientStatistics | null>(null)

  const metrics = {
    total: statistics?.total ?? patients.length,
    active: statistics?.active ?? patients.filter((patient) => patient.is_active).length,
    revenue: patients.reduce((sum, patient) => sum + patient.total_purchases, 0),
    loyalty: statistics ? Object.entries(statistics.by_loyalty_tier).filter(([tier]) => tier !== 'standard').reduce((sum, [, count]) => sum + count, 0) : patients.filter((patient) => patient.loyalty_tier !== 'standard').length,
  }

  useEffect(() => {
    Promise.all([
      apiFetch<Patient[]>('/api/v1/patients/?page=1&page_size=20'),
      apiFetch<PatientStatistics>('/api/v1/patients/statistics'),
    ]).then(([items, stats]) => { setPatients(items); setStatistics(stats) }).catch((err: Error) => setError(err.message)).finally(() => setLoading(false))
  }, [])

  async function openPatient(id: number) {
    try { setError(null); setSelected(await apiFetch<PatientDetail>(`/api/v1/patients/${id}`)) }
    catch (err) { setError(err instanceof Error ? err.message : 'Failed to load patient') }
  }

  if (loading) return <div className='p-6 text-muted-foreground'>Loading patients...</div>

  return (
    <div className='space-y-6 p-6'>
      <div><h1 className='text-2xl font-bold tracking-tight'>Patients</h1><p className='text-muted-foreground'>Pharmacy customer profiles, prescriptions, OTC purchases, cosmetics, vitamins, devices, and receipts.</p></div>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <MetricCard label='Total patients' value={metrics.total.toString()} detail='Registered pharmacy customers' tone='blue' />
        <MetricCard label='Active patients' value={metrics.active.toString()} detail='Currently active profiles' tone='green' />
        <MetricCard label='Purchase value' value={formatCurrency(metrics.revenue)} detail='Synthetic demo portfolio' tone='yellow' />
        <MetricCard label='Loyalty members' value={metrics.loyalty.toString()} detail='Non-standard loyalty tier' tone='red' />
      </div>
      <div className='rounded-2xl border border-border/70 bg-card p-4 shadow-sm'>
        <div className='flex flex-wrap items-center justify-between gap-3'>
          <div><p className='text-sm font-semibold'>Patient pipeline</p><p className='text-xs text-muted-foreground'>Showing first {patients.length} patients from the full database of {metrics.total}</p></div>
          <div className='flex flex-wrap gap-2'>
            {(['blue', 'red', 'green', 'yellow', 'purple', 'orange', 'cyan'] as MetricTone[]).map((tone) => <PipelineBadge key={tone} tone={tone} label={toneLabel(tone)} />)}
          </div>
        </div>
      </div>
      {error && <div className='rounded-lg border p-4 text-sm'>{error}</div>}
      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
        {patients.map((patient) => (
          <button key={patient.id} type='button' onClick={() => openPatient(patient.id)} className='rounded-xl border border-border/70 bg-card p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md'>
            <div className='flex items-start justify-between gap-3'><div><h2 className='font-semibold'>{patient.full_name}</h2><p className='text-sm text-muted-foreground'>{patient.city}, {patient.country}</p></div><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${categoryTone(patient.customer_category)}`}>{patient.customer_category}</span></div>
            <div className='mt-4 grid grid-cols-3 gap-2 text-sm'><div><p className='text-muted-foreground'>Visits</p><p>{patient.visit_count}</p></div><div><p className='text-muted-foreground'>Purchases</p><p>${patient.total_purchases.toFixed(2)}</p></div><div><p className='text-muted-foreground'>Tier</p><p>{patient.loyalty_tier}</p></div></div>
          </button>
        ))}
      </div>
      {selected && (
        <div className='rounded-xl border p-6'>
          <div className='flex items-start justify-between gap-4'><div><h2 className='text-xl font-semibold'>{selected.full_name}</h2><p className='text-sm text-muted-foreground'>{selected.customer_category} · {selected.city}, {selected.country}</p></div><button type='button' className='rounded-md border px-3 py-1 text-sm' onClick={() => setSelected(null)}>Close</button></div>
          <div className='mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
            <MetricCard label='Loyalty points' value={selected.loyalty_points.toLocaleString()} detail={`Tier: ${selected.loyalty_tier}`} tone='blue' />
            <MetricCard label='Total spent' value={formatCurrency(selected.total_purchases)} detail='Lifetime purchase value' tone='yellow' />
            <MetricCard label='Visits' value={selected.visit_count.toString()} detail='Pharmacy visits' tone='green' />
            <MetricCard label='Receipts' value={selected.purchases.length.toString()} detail='Purchase line records' tone='red' />
          </div>
          <div className='mt-6 grid gap-6 lg:grid-cols-2'>
            <section><h3 className='mb-3 font-semibold'>Medical profile</h3>{selected.conditions.length === 0 ? <p className='text-sm text-muted-foreground'>No medical conditions recorded.</p> : <div className='space-y-2'>{selected.conditions.map((condition) => <div key={condition.condition_name} className='rounded-lg border p-3'><p className='font-medium'>{condition.condition_name}</p><p className='text-xs text-muted-foreground'>{condition.status} · {condition.severity}{condition.is_chronic ? ' · chronic' : ''}</p></div>)}</div>}</section>
            <section><h3 className='mb-3 font-semibold'>Purchase history</h3><div className='space-y-2'>{selected.purchases.map((purchase) => <div key={purchase.id} className='rounded-lg border p-3'><div className='flex justify-between gap-3'><p className='font-medium'>{purchase.product_name ?? purchase.category}</p><p>${purchase.total_amount.toFixed(2)}</p></div><p className='text-xs text-muted-foreground'>{purchase.receipt_number} · {purchase.category} · {purchase.prescription_required ? 'Rx' : 'OTC / non-Rx'}</p><p className='mt-1 text-xs text-muted-foreground'>{purchase.dispensed_packs ?? purchase.quantity} pack(s){purchase.dispensed_blisters ? ` · ${purchase.dispensed_blisters} blister(s)` : ''}{purchase.dispensed_units ? ` · ${purchase.dispensed_units} unit(s)` : ''}{purchase.batch_number ? ` · Batch ${purchase.batch_number}` : ''}{purchase.expiry_date ? ` · Exp ${purchase.expiry_date}` : ''}</p></div>)}</div></section>
          </div>
        </div>
      )}
    </div>
  )
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function categoryTone(category: string): string {
  const value = category.toLowerCase()
  if (value.includes('chronic') || value.includes('cardio') || value.includes('diabetes')) return metricToneClass('red')
  if (value.includes('wellness') || value.includes('vitamin') || value.includes('sports')) return metricToneClass('green')
  if (value.includes('skin') || value.includes('cosmetic') || value.includes('women')) return metricToneClass('yellow')
  if (value.includes('prescription') || value.includes('rx') || value.includes('therapy')) return metricToneClass('purple')
  if (value.includes('device') || value.includes('equipment') || value.includes('diagnostic')) return metricToneClass('orange')
  if (value.includes('senior') || value.includes('family') || value.includes('pediatric')) return metricToneClass('cyan')
  return metricToneClass('blue')
}

type MetricTone = 'blue' | 'red' | 'green' | 'yellow' | 'purple' | 'orange' | 'cyan'

function metricToneClass(tone: MetricTone) {
  const classes: Record<MetricTone, string> = {
    blue: 'bg-sky-100 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300',
    green: 'bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-300',
    yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/40 dark:text-yellow-300',
    purple: 'bg-purple-100 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300',
    orange: 'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300',
    cyan: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300',
  }
  return classes[tone]
}

function toneLabel(tone: MetricTone) {
  return tone.charAt(0).toUpperCase() + tone.slice(1)
}

function PipelineBadge({ tone, label }: { tone: MetricTone; label: string }) {
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${metricToneClass(tone)}`}><span className='h-1.5 w-1.5 rounded-full bg-current' />{label}</span>
}

function MetricCard({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: MetricTone }) {
  const tones: Record<MetricTone, string> = {
    blue: 'border-sky-200 bg-sky-50/80 dark:border-sky-900 dark:bg-sky-950/30',
    red: 'border-red-200 bg-red-50/80 dark:border-red-900 dark:bg-red-950/30',
    green: 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-900 dark:bg-emerald-950/30',
    yellow: 'border-amber-200 bg-amber-50/80 dark:border-amber-900 dark:bg-amber-950/30',
    purple: 'border-purple-200 bg-purple-50/80 dark:border-purple-900 dark:bg-purple-950/30',
    orange: 'border-orange-200 bg-orange-50/80 dark:border-orange-900 dark:bg-orange-950/30',
    cyan: 'border-cyan-200 bg-cyan-50/80 dark:border-cyan-900 dark:bg-cyan-950/30',
  }
  const dots: Record<MetricTone, string> = {
    blue: 'bg-sky-500',
    red: 'bg-red-500',
    green: 'bg-emerald-500',
    yellow: 'bg-amber-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    cyan: 'bg-cyan-500',
  }

  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${tones[tone]}`}>
      <div className='flex items-center gap-2'>
        <span className={`h-2.5 w-2.5 rounded-full ${dots[tone]}`} />
        <p className='text-sm font-medium'>{label}</p>
      </div>
      <p className='mt-3 text-3xl font-bold tracking-tight'>{value}</p>
      <p className='mt-1 text-xs text-muted-foreground'>{detail}</p>
    </div>
  )
}