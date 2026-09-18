import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { apiFetch } from '@/lib/api-client'

type Patient = { id: number; full_name: string; phone: string; email?: string; city?: string; country: string; customer_category: string; loyalty_tier: string; total_purchases: number; visit_count: number; is_active: boolean }
type PatientDetail = Patient & { conditions: Array<{ condition_name: string; severity: string; status: string; is_chronic: boolean }>; purchases: Array<{ id: number; receipt_number: string; category: string; product_id?: number; product_name?: string; batch_number?: string; expiry_date?: string; quantity: number; dispensed_packs?: number; dispensed_blisters?: number; dispensed_units?: number; unit_price: number; total_amount: number; prescription_required: boolean; purchased_at: string }> }

export const Route = createFileRoute('/_authenticated/patients')({ component: PatientsPage })

function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selected, setSelected] = useState<PatientDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<Patient[]>('/api/v1/patients/?page=1&page_size=100').then(setPatients).catch((err: Error) => setError(err.message)).finally(() => setLoading(false))
  }, [])

  async function openPatient(id: number) {
    try { setError(null); setSelected(await apiFetch<PatientDetail>(`/api/v1/patients/${id}`)) }
    catch (err) { setError(err instanceof Error ? err.message : 'Failed to load patient') }
  }

  if (loading) return <div className='p-6 text-muted-foreground'>Loading patients...</div>

  return (
    <div className='space-y-6 p-6'>
      <div><h1 className='text-2xl font-bold tracking-tight'>Patients</h1><p className='text-muted-foreground'>Pharmacy customer profiles, prescriptions, OTC purchases, cosmetics, vitamins, devices, and receipts.</p></div>
      {error && <div className='rounded-lg border p-4 text-sm'>{error}</div>}
      <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
        {patients.map((patient) => (
          <button key={patient.id} type='button' onClick={() => openPatient(patient.id)} className='rounded-xl border p-4 text-left transition hover:bg-muted/50'>
            <div className='flex items-start justify-between gap-3'><div><h2 className='font-semibold'>{patient.full_name}</h2><p className='text-sm text-muted-foreground'>{patient.city}, {patient.country}</p></div><span className='rounded-full border px-2 py-1 text-xs'>{patient.customer_category}</span></div>
            <div className='mt-4 grid grid-cols-3 gap-2 text-sm'><div><p className='text-muted-foreground'>Visits</p><p>{patient.visit_count}</p></div><div><p className='text-muted-foreground'>Purchases</p><p>${patient.total_purchases.toFixed(2)}</p></div><div><p className='text-muted-foreground'>Tier</p><p>{patient.loyalty_tier}</p></div></div>
          </button>
        ))}
      </div>
      {selected && (
        <div className='rounded-xl border p-6'>
          <div className='flex items-start justify-between gap-4'><div><h2 className='text-xl font-semibold'>{selected.full_name}</h2><p className='text-sm text-muted-foreground'>{selected.customer_category} · {selected.city}, {selected.country}</p></div><button type='button' className='rounded-md border px-3 py-1 text-sm' onClick={() => setSelected(null)}>Close</button></div>
          <div className='mt-6 grid gap-6 lg:grid-cols-2'>
            <section><h3 className='mb-3 font-semibold'>Medical profile</h3>{selected.conditions.length === 0 ? <p className='text-sm text-muted-foreground'>No medical conditions recorded.</p> : <div className='space-y-2'>{selected.conditions.map((condition) => <div key={condition.condition_name} className='rounded-lg border p-3'><p className='font-medium'>{condition.condition_name}</p><p className='text-xs text-muted-foreground'>{condition.status} · {condition.severity}{condition.is_chronic ? ' · chronic' : ''}</p></div>)}</div>}</section>
            <section><h3 className='mb-3 font-semibold'>Purchase history</h3><div className='space-y-2'>{selected.purchases.map((purchase) => <div key={purchase.id} className='rounded-lg border p-3'><div className='flex justify-between gap-3'><p className='font-medium'>{purchase.product_name ?? purchase.category}</p><p>${purchase.total_amount.toFixed(2)}</p></div><p className='text-xs text-muted-foreground'>{purchase.receipt_number} · {purchase.category} · {purchase.prescription_required ? 'Rx' : 'OTC / non-Rx'}</p><p className='mt-1 text-xs text-muted-foreground'>{purchase.dispensed_packs ?? purchase.quantity} pack(s){purchase.dispensed_blisters ? ` · ${purchase.dispensed_blisters} blister(s)` : ''}{purchase.dispensed_units ? ` · ${purchase.dispensed_units} unit(s)` : ''}{purchase.batch_number ? ` · Batch ${purchase.batch_number}` : ''}{purchase.expiry_date ? ` · Exp ${purchase.expiry_date}` : ''}</p></div>)}</div></section>
          </div>
        </div>
      )}
    </div>
  )
}