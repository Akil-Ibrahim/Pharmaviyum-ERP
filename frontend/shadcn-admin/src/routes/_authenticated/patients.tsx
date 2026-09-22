import { useEffect, useState } from 'react'
import { Activity, HeartPulse, ShieldCheck, ShoppingBag } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { apiFetch } from '@/lib/api-client'

type Patient = { id: number; full_name: string; phone: string; email?: string; city?: string; country: string; customer_category: string; loyalty_tier: string; visit_count: number; is_active: boolean }
type PatientStatistics = { total: number; active: number; inactive: number; total_purchase_value: number; total_loyalty_points: number; by_loyalty_tier: Record<string, number>; by_country: Record<string, number> }
type PatientDetail = Patient & {
  first_name: string
  last_name: string
  loyalty_points: number
  address?: string
  date_of_birth?: string
  gender?: string
  blood_type?: string
  preferred_language?: string
  notes?: string
  last_visit_date?: string
  created_at: string
  updated_at: string
  conditions: Array<{ condition_name: string; icd10_code?: string; severity: string; status: string; is_chronic: boolean; diagnosis_date?: string; treatment_notes?: string; current_medications?: string; notes?: string; created_at: string; updated_at: string }>
  allergies: Array<{ id: number; allergen_type: string; allergen_name: string; severity: string; reaction?: string; is_verified: boolean; created_at: string; updated_at: string }>
  insurances: Array<{ id: number; provider_name: string; policy_number?: string; is_active: boolean; created_at: string; updated_at: string }>
  consultations: Array<{ id: number; notes?: string; created_at: string; updated_at: string }>
  purchases: Array<{ id: number; receipt_number: string; category: string; product_id?: number; product_name?: string; batch_id?: number; batch_number?: string; expiry_date?: string; quantity: number; dispensed_packs?: number; dispensed_blisters?: number; dispensed_units?: number; unit_price: number; total_amount: number; prescription_required: boolean; purchased_at: string }>
}

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
    revenue: statistics?.total_purchase_value ?? 0,
    loyalty: statistics ? Object.entries(statistics.by_loyalty_tier).filter(([tier]) => tier.toLowerCase() !== 'standard').reduce((sum, [, count]) => sum + count, 0) : patients.filter((patient) => patient.loyalty_tier.toLowerCase() !== 'standard').length,
  }

  useEffect(() => {
    Promise.allSettled([
      apiFetch<Patient[]>('/api/v1/patients/?page=1&page_size=20'),
      apiFetch<PatientStatistics>('/api/v1/patients/statistics'),
    ]).then(([patientsResult, statisticsResult]) => {
      if (patientsResult.status === 'fulfilled') setPatients(patientsResult.value)
      else setError(patientsResult.reason instanceof Error ? patientsResult.reason.message : 'Failed to load patients')
      if (statisticsResult.status === 'fulfilled') setStatistics(statisticsResult.value)
    }).finally(() => setLoading(false))
  }, [])

  async function openPatient(id: number) {
    try { setError(null); setSelected(await apiFetch<PatientDetail>(`/api/v1/patients/${id}`)) }
    catch (err) { setError(err instanceof Error ? err.message : 'Failed to load patient') }
  }

  if (loading) return <div className='p-6 text-muted-foreground'>Loading patients...</div>

  return (
    <div className='space-y-6 p-6'>
      <div><p className='text-xs font-semibold uppercase tracking-[0.18em] text-primary'>Pharmaviyum entity</p><h1 className='mt-1 text-2xl font-bold tracking-tight text-foreground'>Patients</h1><p className='text-muted-foreground'>Pharmacy customer profiles, prescriptions, OTC purchases, cosmetics, vitamins, devices, and receipts.</p></div>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <CircleMetric icon={HeartPulse} label='Total patients' value={metrics.total} />
        <CircleMetric icon={Activity} label='Active patients' value={metrics.active} />
        <CircleMetric icon={ShoppingBag} label='Purchase value' value={metrics.revenue} currency />
        <CircleMetric icon={ShieldCheck} label='Loyalty members' value={metrics.loyalty} />
        <div className='hidden'>
        <MetricCard label='Total patients' value={metrics.total.toString()} detail='Full database · first 20 displayed' tone='blue' />
        <MetricCard label='Active patients' value={metrics.active.toString()} detail='Currently active profiles' tone='green' />
        <MetricCard label='Purchase value' value={formatCurrency(metrics.revenue)} detail='Full persisted purchase history' tone='yellow' />
        <MetricCard label='Loyalty members' value={metrics.loyalty.toString()} detail='Non-standard loyalty tier' tone='red' />
      </div></div>
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
            <div className='flex items-start justify-between gap-3'><div><h2 className='text-base font-semibold tracking-tight text-foreground'>{patient.full_name}</h2><p className='text-sm text-muted-foreground'>{patient.city}, {patient.country}</p></div><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${categoryTone(patient.customer_category)}`}>{patient.customer_category}</span></div>
            <div className='mt-4 grid grid-cols-3 gap-2 text-sm'><div><p className='text-muted-foreground'>Visits</p><p>{patient.visit_count}</p></div><div><p className='text-muted-foreground'>Status</p><p>{patient.is_active ? 'Active' : 'Inactive'}</p></div><div><p className='text-muted-foreground'>Tier</p><p>{patient.loyalty_tier}</p></div></div>
          </button>
        ))}
      </div>
      {selected && (
        <div className='rounded-xl border p-6'>
          <div className='flex items-start justify-between gap-4'><div><h2 className='text-xl font-semibold tracking-tight text-foreground'>{selected.full_name}</h2><p className='text-sm text-muted-foreground'>{selected.customer_category} · {selected.city}, {selected.country}</p></div><button type='button' className='rounded-md border px-3 py-1 text-sm' onClick={() => setSelected(null)}>Close</button></div>
          <div className='mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
            <MetricCard label='Loyalty points' value={selected.loyalty_points.toLocaleString()} detail={`Tier: ${selected.loyalty_tier}`} tone='blue' />
            <MetricCard label='Total spent' value={formatCurrency(selected.purchases.reduce((sum, purchase) => sum + purchase.total_amount, 0))} detail='Persisted purchase history' tone='yellow' />
            <MetricCard label='Visits' value={selected.visit_count.toString()} detail='Pharmacy visits' tone='green' />
            <MetricCard label='Receipts' value={new Set(selected.purchases.map((purchase) => purchase.receipt_number)).size.toString()} detail='Unique persisted receipts' tone='red' />
          </div>
          <div className='mt-6 grid gap-6 lg:grid-cols-3'>
            <section className='rounded-xl border p-4'><h3 className='mb-3 font-semibold'>Patient profile</h3><div className='space-y-2 text-sm'>
              <p><span className='text-muted-foreground'>Phone:</span> {selected.phone}</p><p><span className='text-muted-foreground'>Email:</span> {selected.email ?? '—'}</p><p><span className='text-muted-foreground'>Gender:</span> {selected.gender ?? '—'}</p><p><span className='text-muted-foreground'>Date of birth:</span> {selected.date_of_birth ?? '—'}</p><p><span className='text-muted-foreground'>Blood type:</span> {selected.blood_type ?? '—'}</p><p><span className='text-muted-foreground'>Language:</span> {selected.preferred_language ?? '—'}</p><p><span className='text-muted-foreground'>Last visit:</span> {formatDateTime(selected.last_visit_date)}</p><p><span className='text-muted-foreground'>Profile created:</span> {formatDateTime(selected.created_at)}</p>{selected.notes && <p className='pt-2 text-muted-foreground'>{selected.notes}</p>}</div></section>
            <section className='rounded-xl border p-4'><h3 className='mb-3 font-semibold'>Allergies & insurance</h3><div className='space-y-3'>
              <div><p className='text-xs font-semibold uppercase text-muted-foreground'>Allergies</p>{selected.allergies.length === 0 ? <p className='mt-1 text-sm text-muted-foreground'>None recorded.</p> : <div className='mt-2 space-y-2'>{selected.allergies.map((a) => <div key={a.id} className='rounded-lg border p-2'><p className='font-medium'>{a.allergen_name}</p><p className='text-xs text-muted-foreground'>{a.allergen_type} · {a.severity}{a.reaction ? ` · ${a.reaction}` : ''}{a.is_verified ? ' · verified' : ''}</p></div>)}</div>}</div>
              <div><p className='text-xs font-semibold uppercase text-muted-foreground'>Insurance</p>{selected.insurances.length === 0 ? <p className='mt-1 text-sm text-muted-foreground'>None recorded.</p> : <div className='mt-2 space-y-2'>{selected.insurances.map((i) => <div key={i.id} className='rounded-lg border p-2'><p className='font-medium'>{i.provider_name}</p><p className='text-xs text-muted-foreground'>{i.policy_number ?? 'No policy number'} · {i.is_active ? 'Active' : 'Inactive'}</p></div>)}</div>}</div>
            </div></section>
            <section className='rounded-xl border p-4'><h3 className='mb-3 font-semibold'>Medical profile</h3>{selected.conditions.length === 0 ? <p className='text-sm text-muted-foreground'>No medical conditions recorded.</p> : <div className='space-y-2'>{selected.conditions.map((condition) => <div key={condition.condition_name} className='rounded-lg border p-3'><p className='font-medium'>{condition.condition_name}</p><p className='text-xs text-muted-foreground'>{condition.status} · {condition.severity}{condition.is_chronic ? ' · chronic' : ''}</p>{condition.diagnosis_date && <p className='mt-1 text-xs text-muted-foreground'>Diagnosed: {condition.diagnosis_date}</p>}{condition.current_medications && <p className='mt-1 text-xs'>{condition.current_medications}</p>}</div>)}</div>}</section>
          </div>
          <section className='mt-6 rounded-xl border p-4'>
            <div className='flex items-center justify-between gap-3'>
              <div>
                <h3 className='font-semibold'>Receipts & purchase history</h3>
                <p className='text-xs text-muted-foreground'>Every persisted receipt line for this patient, grouped by receipt number.</p>
              </div>
              <span className='rounded-full bg-muted px-2.5 py-1 text-xs'>{selected.purchases.length} line records</span>
            </div>
            <div className='mt-4 space-y-3'>
              {groupReceipts(selected.purchases).map((receipt) => (
                <div key={receipt.receiptNumber} className='rounded-xl border p-4'>
                  <div className='flex flex-wrap items-start justify-between gap-3'>
                    <div>
                      <p className='font-semibold'>Receipt {receipt.receiptNumber}</p>
                      <p className='text-xs text-muted-foreground'>{formatDateTime(receipt.purchasedAt)} · {receipt.lines.length} item(s)</p>
                    </div>
                    <p className='text-lg font-bold'>{formatCurrency(receipt.total)}</p>
                  </div>
                  <div className='mt-3 space-y-2'>
                    {receipt.lines.map((item) => (
                      <div key={item.id} className='rounded-lg bg-muted/40 p-3'>
                        <div className='flex flex-wrap items-start justify-between gap-3'>
                          <div>
                            <p className='font-medium'>{item.product_name ?? item.category}</p>
                            <p className='text-xs text-muted-foreground'>{item.category} · {item.prescription_required ? 'Rx' : 'OTC / non-Rx'}</p>
                          </div>
                          <p className='font-medium'>{formatCurrency(item.total_amount)}</p>
                        </div>
                        <p className='mt-2 text-xs text-muted-foreground'>
                          {item.dispensed_packs ?? item.quantity} pack(s)
                          {item.dispensed_blisters ? ' · ' + item.dispensed_blisters + ' blister(s)' : ''}
                          {item.dispensed_units ? ' · ' + item.dispensed_units + ' unit(s)' : ''}
                          {item.batch_number ? ' · Batch ' + item.batch_number : ''}
                          {item.expiry_date ? ' · Exp ' + item.expiry_date : ''}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {selected.purchases.length === 0 && <p className='text-sm text-muted-foreground'>No receipts are recorded for this patient.</p>}
            </div>
          </section>
          <section className='mt-6 rounded-xl border p-4'>
            <div className='flex items-center justify-between gap-3'>
              <div>
                <h3 className='font-semibold'>Full patient history</h3>
                <p className='text-xs text-muted-foreground'>All persisted consultations and purchase records for this patient.</p>
              </div>
              <span className='rounded-full bg-muted px-2.5 py-1 text-xs'>{selected.consultations.length + selected.purchases.length} events</span>
            </div>
            <div className='mt-4 space-y-3'>
              {selected.consultations.length === 0 && selected.purchases.length === 0 ? <p className='text-sm text-muted-foreground'>No history records are available.</p> : [
                ...selected.consultations.map((item) => ({ kind: 'Consultation', date: item.created_at, id: 'c-' + item.id, title: 'Consultation', detail: item.notes ?? 'Consultation recorded.' })),
                ...selected.purchases.map((item) => ({ kind: item.prescription_required ? 'Prescription' : 'Purchase', date: item.purchased_at, id: 'p-' + item.id, title: item.product_name ?? item.category, detail: item.receipt_number + ' · ' + formatCurrency(item.total_amount) + ' · ' + item.category })),
              ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).map((event) => (
                <div key={event.id} className='flex gap-3 rounded-lg border p-3'>
                  <div className='mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-sky-500' />
                  <div className='min-w-0'>
                    <div className='flex flex-wrap gap-x-2 gap-y-1'><p className='font-medium'>{event.title}</p><span className='text-xs text-muted-foreground'>{event.kind}</span></div>
                    <p className='text-sm text-muted-foreground'>{event.detail}</p>
                    <p className='mt-1 text-xs text-muted-foreground'>{formatDateTime(event.date)}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value)
}

function formatDateTime(value?: string) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function groupReceipts(purchases: PatientDetail['purchases']) {
  const grouped = new Map<string, { receiptNumber: string; purchasedAt: string; total: number; lines: PatientDetail['purchases'] }>()
  for (const purchase of purchases) {
    const current = grouped.get(purchase.receipt_number)
    if (current) {
      current.total += purchase.total_amount
      current.lines.push(purchase)
    } else {
      grouped.set(purchase.receipt_number, {
        receiptNumber: purchase.receipt_number,
        purchasedAt: purchase.purchased_at,
        total: purchase.total_amount,
        lines: [purchase],
      })
    }
  }
  return Array.from(grouped.values()).sort((a, b) => new Date(b.purchasedAt).getTime() - new Date(a.purchasedAt).getTime())
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

function CircleMetric({icon:Icon,label,value,currency=false}:{icon:typeof HeartPulse;label:string;value:number;currency?:boolean}){
 const display=currency?formatCurrency(value):value.toLocaleString()
 return <div className='rounded-2xl border bg-card p-4 shadow-sm'><div className='flex items-center gap-4'><div className='relative flex size-14 shrink-0 items-center justify-center rounded-full bg-primary/10'><div className='flex size-10 items-center justify-center rounded-full bg-card'><Icon className='size-4 text-primary'/></div></div><div><p className='text-xs text-muted-foreground'>{label}</p><p className='text-xl font-bold text-foreground'>{display}</p></div></div></div>
}
