import { useEffect, useMemo, useState, type KeyboardEvent } from 'react'
import {
  Barcode, CheckCircle2, Minus, Package, Plus, RefreshCw, Search,
  ShieldAlert, ShoppingCart, Trash2, UserRound, XCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type Pharmacy = { id: number; name: string; code?: string; is_active?: boolean }
type Patient = { id: number; full_name: string; phone: string; pharmacy_id?: number | null; is_active: boolean }
type PosProduct = {
  id: number
  name: string
  sku: string
  barcode?: string | null
  gtin?: string | null
  inn_name?: string | null
  strength?: string | null
  form?: string | null
  manufacturer?: string | null
  units_per_pack: number
  price: number
  prescription_required: boolean
  available_quantity: number
  earliest_expiry?: string | null
}
type CartItem = PosProduct & { quantity: number }
type Receipt = {
  order_id: number
  receipt_number: string
  patient_name: string
  payment_method: string
  total_amount: number
  items: Array<{ product_name: string; quantity: number; unit_price: number; line_total: number; batch_number?: string | null }>
}

const money = (value: number) => new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2, maximumFractionDigits: 2,
}).format(value)

export function Pos() {
  const [pharmacies, setPharmacies] = useState<Pharmacy[]>([])
  const [pharmacyId, setPharmacyId] = useState('')
  const [patients, setPatients] = useState<Patient[]>([])
  const [patientId, setPatientId] = useState('')
  const [products, setProducts] = useState<PosProduct[]>([])
  const [query, setQuery] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [loading, setLoading] = useState(true)
  const [checkingOut, setCheckingOut] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [receipt, setReceipt] = useState<Receipt | null>(null)

  const loadSetup = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      apiFetch<Pharmacy[]>('/api/v1/pharmacies'),
      apiFetch<Patient[]>('/api/v1/patients/?page=1&page_size=100'),
    ]).then(([pharmacyRows, patientRows]) => {
      const activePharmacies = pharmacyRows.filter((item) => item.is_active !== false)
      setPharmacies(activePharmacies)
      setPharmacyId((current) => current || (activePharmacies[0] ? String(activePharmacies[0].id) : ''))
      setPatients(patientRows.filter((item) => item.is_active))
    }).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : 'Unable to load POS setup data')
    }).finally(() => setLoading(false))
  }

  const loadCatalog = () => {
    if (!pharmacyId) {
      setProducts([])
      return
    }
    setError(null)
    apiFetch<PosProduct[]>(`/api/v1/pos/catalog?pharmacy_id=${encodeURIComponent(pharmacyId)}`)
      .then(setProducts)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load pharmacy stock'))
  }

  useEffect(() => { loadSetup() }, [])
  useEffect(() => { loadCatalog() }, [pharmacyId])

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return products
    return products.filter((product) =>
      [product.name, product.sku, product.barcode ?? '', product.gtin ?? '',
        product.inn_name ?? '', product.strength ?? '', product.manufacturer ?? '']
        .some((value) => value.toLowerCase().includes(q)),
    )
  }, [products, query])

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0)
  const selectedPatient = patients.find((patient) => String(patient.id) === patientId)

  const addToCart = (product: PosProduct) => {
    if (product.available_quantity < 1) return
    setReceipt(null)
    setCart((items) => {
      const current = items.find((item) => item.id === product.id)
      if (current) return items.map((item) => item.id === product.id
        ? { ...item, quantity: Math.min(item.quantity + 1, product.available_quantity) }
        : item)
      return [...items, { ...product, quantity: 1 }]
    })
  }

  const updateQuantity = (id: number, delta: number) => {
    setCart((items) => items.flatMap((item) => {
      if (item.id !== id) return [item]
      const quantity = item.quantity + delta
      return quantity > 0
        ? [{ ...item, quantity: Math.min(quantity, item.available_quantity) }]
        : []
    }))
  }

  const scanEnter = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter') return
    const value = query.trim().toLowerCase()
    if (!value) return
    const exact = products.find((product) =>
      [product.barcode, product.gtin, product.sku].some((code) => code?.toLowerCase() === value),
    )
    if (exact) {
      addToCart(exact)
      setQuery('')
    } else if (results.length === 1) {
      addToCart(results[0])
      setQuery('')
    }
  }

  const checkout = async () => {
    if (!pharmacyId || !patientId || cart.length === 0 || checkingOut) return
    setCheckingOut(true)
    setError(null)
    try {
      const result = await apiFetch<Receipt>('/api/v1/pos/checkout', {
        method: 'POST',
        body: JSON.stringify({
          pharmacy_id: Number(pharmacyId),
          patient_id: Number(patientId),
          payment_method: paymentMethod,
          items: cart.map(({ id, quantity }) => ({ product_id: id, quantity })),
        }),
      })
      setReceipt(result)
      setCart([])
      setQuery('')
      loadCatalog()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed; no sale was recorded.')
    } finally {
      setCheckingOut(false)
    }
  }

  return (
    <div className='space-y-6 p-4 sm:p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Point of Sale</h1>
          <p className='text-muted-foreground'>Live pharmacy catalog, FEFO stock allocation, patient and receipt history.</p>
        </div>
        <div className='flex flex-wrap items-center gap-2'>
          <Badge variant='outline' className='gap-2 px-3 py-1.5'>
            <span className='size-2 rounded-full bg-emerald-500' /> Live inventory
          </Badge>
          <Button variant='outline' size='sm' onClick={() => { loadCatalog(); loadSetup() }} disabled={loading || checkingOut}>
            <RefreshCw className='mr-2 size-4' /> Refresh
          </Button>
        </div>
      </div>

      {error && <div role='alert' className='flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive'><ShieldAlert className='mt-0.5 size-4 shrink-0'/><span>{error}</span></div>}

      {receipt && <Card className='border-emerald-500/40'>
        <CardContent className='flex flex-col gap-3 p-4 sm:flex-row sm:items-start sm:justify-between'>
          <div className='flex gap-3'><CheckCircle2 className='mt-0.5 size-5 text-emerald-600'/><div>
            <p className='font-semibold'>Sale recorded successfully</p>
            <p className='text-sm text-muted-foreground'>{receipt.receipt_number} · {receipt.patient_name} · {receipt.payment_method}</p>
            <p className='mt-1 text-lg font-bold'>{money(receipt.total_amount)}</p>
            <p className='text-xs text-muted-foreground'>Stock deductions, patient purchase history and audit event were committed together.</p>
          </div></div>
          <Button variant='outline' size='sm' onClick={() => setReceipt(null)}>Dismiss</Button>
        </CardContent>
      </Card>}

      <div className='grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]'>
        <div className='space-y-5'>
          <Card>
            <CardHeader className='space-y-4'>
              <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
                <CardTitle>Find a medicine or product</CardTitle>
                <div className='w-full sm:max-w-xs'>
                  <label className='sr-only' htmlFor='pos-pharmacy'>Pharmacy</label>
                  <select id='pos-pharmacy' value={pharmacyId} onChange={(event) => { setPharmacyId(event.target.value); setCart([]); setReceipt(null) }}
                    className='h-10 w-full rounded-md border bg-background px-3 text-sm' disabled={loading || pharmacies.length === 0}>
                    {pharmacies.length === 0 && <option value=''>No pharmacy available</option>}
                    {pharmacies.map((pharmacy) => <option key={pharmacy.id} value={pharmacy.id}>{pharmacy.name}</option>)}
                  </select>
                </div>
              </div>
              <div className='relative'>
                <Search className='absolute left-3 top-3 size-4 text-muted-foreground'/>
                <Input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={scanEnter}
                  placeholder='Scan barcode or search name, INN, brand, SKU...' className='pl-9' autoComplete='off'/>
              </div>
            </CardHeader>
            <CardContent className='space-y-3'>
              {loading && <p className='py-8 text-center text-sm text-muted-foreground'>Loading pharmacy and patient data…</p>}
              {!loading && results.map((product) => (
                <button key={product.id} type='button' onClick={() => addToCart(product)}
                  disabled={product.available_quantity < 1}
                  className='w-full rounded-lg border p-4 text-left transition-colors hover:bg-muted/40 disabled:cursor-not-allowed disabled:opacity-55'>
                  <div className='flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between'>
                    <div className='min-w-0'>
                      <div className='flex flex-wrap items-center gap-2'>
                        <p className='font-semibold'>{product.name}</p>
                        <Badge variant={product.prescription_required ? 'destructive' : 'secondary'}>
                          {product.prescription_required ? 'Prescription required' : 'OTC / non-Rx'}
                        </Badge>
                      </div>
                      <p className='mt-1 text-sm text-muted-foreground'>{[product.inn_name, product.strength, product.form].filter(Boolean).join(' · ') || product.sku}</p>
                      <p className='text-sm text-muted-foreground'>{product.manufacturer || 'Manufacturer not specified'} · SKU {product.sku}</p>
                    </div>
                    <div className='shrink-0 sm:text-right'>
                      <p className='font-semibold'>{money(product.price)}</p>
                      <p className={product.available_quantity < 1 ? 'text-xs text-destructive' : 'text-xs text-muted-foreground'}>
                        Available {product.available_quantity}
                      </p>
                      {product.earliest_expiry && <p className='text-xs text-muted-foreground'>Earliest expiry {product.earliest_expiry}</p>}
                    </div>
                  </div>
                </button>
              ))}
              {!loading && results.length === 0 && <div className='rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground'>
                <Package className='mx-auto mb-2 size-5'/>{products.length ? 'No matching products.' : 'No live stock records for this pharmacy.'}
              </div>}
            </CardContent>
          </Card>
        </div>

        <Card className='h-fit xl:sticky xl:top-4'>
          <CardHeader>
            <div className='flex items-center justify-between gap-2'>
              <CardTitle className='flex items-center gap-2'><ShoppingCart className='size-5'/> Current receipt</CardTitle>
              <Badge variant='outline'>{totalQuantity} units</Badge>
            </div>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='space-y-2'>
              <label htmlFor='pos-patient' className='flex items-center gap-2 text-sm font-medium'><UserRound className='size-4'/> Patient / customer</label>
              <select id='pos-patient' value={patientId} onChange={(event) => setPatientId(event.target.value)}
                className='h-10 w-full rounded-md border bg-background px-3 text-sm'>
                <option value=''>Select a patient…</option>
                {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.full_name} · {patient.phone}</option>)}
              </select>
              <p className='text-xs text-muted-foreground'>Select a patient to keep purchase history and validate prescriptions.</p>
            </div>

            {cart.length === 0 ? <div className='rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground'>
              Scan or select an item to start a receipt.
            </div> : <div className='max-h-[42vh] space-y-3 overflow-y-auto pr-1'>
              {cart.map((item) => <div key={item.id} className='rounded-lg border p-3'>
                <div className='flex items-start justify-between gap-2'>
                  <div className='min-w-0'><p className='font-medium'>{item.name}</p>
                    <p className='text-xs text-muted-foreground'>{money(item.price)} each · stock {item.available_quantity}</p></div>
                  <Button variant='ghost' size='icon' className='size-8 shrink-0' aria-label={`Remove ${item.name}`}
                    onClick={() => setCart((items) => items.filter((entry) => entry.id !== item.id))}><Trash2 className='size-4'/></Button>
                </div>
                <div className='mt-3 flex items-center justify-between gap-3'>
                  <div className='flex items-center gap-1'>
                    <Button variant='outline' size='icon' className='size-8' aria-label='Decrease quantity' onClick={() => updateQuantity(item.id, -1)}><Minus className='size-3'/></Button>
                    <span className='w-8 text-center text-sm'>{item.quantity}</span>
                    <Button variant='outline' size='icon' className='size-8' aria-label='Increase quantity' disabled={item.quantity >= item.available_quantity} onClick={() => updateQuantity(item.id, 1)}><Plus className='size-3'/></Button>
                  </div>
                  <span className='font-semibold'>{money(item.price * item.quantity)}</span>
                </div>
              </div>)}
            </div>}

            <div className='space-y-2'>
              <label htmlFor='pos-payment' className='text-sm font-medium'>Payment method</label>
              <select id='pos-payment' value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}
                className='h-10 w-full rounded-md border bg-background px-3 text-sm'>
                <option value='cash'>Cash</option><option value='card'>Card</option><option value='mobile'>Mobile payment</option><option value='other'>Other</option>
              </select>
            </div>
            <div className='space-y-2 border-t pt-4'>
              <div className='flex justify-between text-sm text-muted-foreground'><span>Items</span><span>{totalQuantity}</span></div>
              <div className='flex items-center justify-between text-lg font-bold'><span>Total</span><span>{money(total)}</span></div>
            </div>
            <Button className='w-full' size='lg' onClick={checkout} disabled={!cart.length || !patientId || !pharmacyId || checkingOut}>
              {checkingOut ? 'Processing sale…' : 'Complete sale'}
            </Button>
            <Button variant='outline' className='w-full' onClick={() => { setCart([]); setReceipt(null) }} disabled={!cart.length || checkingOut}>
              <XCircle className='mr-2 size-4'/> Clear receipt
            </Button>
            <p className='text-xs text-muted-foreground'>Checkout checks stock and active prescriptions for Rx products. Expired lots and stock mismatches are rejected; successful sales are audited.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
