import { useEffect, useMemo, useState } from 'react'
import { Barcode, Minus, Plus, Search, ShoppingCart, Trash2, UserRound } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type PosProduct = {
  id: number
  name: string
  genericName: string
  strength: string
  form: string
  manufacturer: string
  stock: number
  price: number
  batch: string
  expiry: string
  kind: 'Reference Product' | 'Generic Product'
}

type DrugCatalogResult = {
  medicinal_product_id: number
  drug_reference_id: number
  inn_name: string
  atc_code: string | null
  ingredient_names: string[]
  brand_name: string | null
  product_type: string
  manufacturer: string | null
  strength: string | null
  dosage_form: string | null
  route: string | null
  package_description: string | null
  gtin: string | null
  regulatory_id: string | null
}

type CartItem = PosProduct & { quantity: number }

const catalog: PosProduct[] = [
  { id: 1, name: 'Omeprazole 20 mg', genericName: 'Omeprazole', strength: '20 mg', form: 'Capsule · 30', manufacturer: 'AstraZeneca', stock: 12, price: 8.5, batch: 'OM-1026-A', expiry: '2026-10', kind: 'Reference Product' },
  { id: 2, name: 'Omeprazole 20 mg', genericName: 'Omeprazole', strength: '20 mg', form: 'Capsule · 30', manufacturer: 'Pharma Generic A', stock: 24, price: 5.9, batch: 'OM-0427-B', expiry: '2027-04', kind: 'Generic Product' },
  { id: 3, name: 'Omeprazole 40 mg', genericName: 'Omeprazole', strength: '40 mg', form: 'Capsule · 30', manufacturer: 'Pharma Generic B', stock: 8, price: 7.2, batch: 'OM-1127-C', expiry: '2027-11', kind: 'Generic Product' },
  { id: 4, name: 'Paracetamol 500 mg', genericName: 'Paracetamol', strength: '500 mg', form: 'Tablet · 20', manufacturer: 'Pharma Generic C', stock: 31, price: 3.4, batch: 'PA-0627-A', expiry: '2027-06', kind: 'Generic Product' },
]

export function Pos() {
  const [query, setQuery] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>([])
  const [referenceLoading, setReferenceLoading] = useState(false)
  const [referenceError, setReferenceError] = useState(false)

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) {
      setReferenceResults([])
      setReferenceLoading(false)
      setReferenceError(false)
      return
    }

    let cancelled = false
    setReferenceLoading(true)
    setReferenceError(false)
    apiFetch<DrugCatalogResult[]>(
      `/api/v1/drug-catalog/search?q=${encodeURIComponent(term)}&limit=8`,
    )
      .then((items) => {
        if (!cancelled) setReferenceResults(items)
      })
      .catch(() => {
        if (!cancelled) {
          setReferenceResults([])
          setReferenceError(true)
        }
      })
      .finally(() => {
        if (!cancelled) setReferenceLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [query])

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return catalog
    return catalog.filter((p) =>
      [p.name, p.genericName, p.strength, p.form, p.manufacturer, p.batch].some((v) => v.toLowerCase().includes(q)),
    )
  }, [query])

  const addToCart = (product: PosProduct) => {
    setCart((items) => {
      const existing = items.find((item) => item.id === product.id)
      if (existing) {
        return items.map((item) => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item)
      }
      return [...items, { ...product, quantity: 1 }]
    })
  }

  const updateQuantity = (id: number, delta: number) => {
    setCart((items) => items.flatMap((item) => {
      if (item.id !== id) return [item]
      const quantity = item.quantity + delta
      return quantity > 0 ? [{ ...item, quantity: Math.min(quantity, item.stock) }] : []
    }))
  }

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  return (
    <div className='space-y-6 p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>POS</h1>
          <p className='text-muted-foreground'>Point of Sale for fast pharmacy dispensing and checkout.</p>
        </div>
        <Badge variant='outline' className='w-fit gap-2 px-3 py-1.5'>
          <span className='size-2 rounded-full bg-emerald-500' /> Register 1 · Open
        </Badge>
      </div>

      <div className='grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]'>
        <Card>
          <CardHeader className='space-y-4'>
            <div className='flex items-center justify-between gap-3'>
              <CardTitle>Product Search</CardTitle>
              <Button variant='outline' size='sm'><Barcode className='mr-2 size-4' />Scan</Button>
            </div>
            <div className='relative'>
              <Search className='absolute left-3 top-3 size-4 text-muted-foreground' />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder='Search by name, INN, brand, manufacturer, barcode or SKU...' className='pl-9' />
            </div>
          </CardHeader>
          <CardContent className='space-y-3'>
            <p className='text-sm font-medium'>Local products</p>
            {results.map((product) => (
              <button key={product.id} type='button' onClick={() => addToCart(product)} className='w-full rounded-lg border p-4 text-left transition-colors hover:bg-muted/50'>
                <div className='flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between'>
                  <div>
                    <div className='flex flex-wrap items-center gap-2'>
                      <p className='font-semibold'>{product.name}</p>
                      <Badge variant='secondary'>{product.kind}</Badge>
                    </div>
                    <p className='mt-1 text-sm text-muted-foreground'>INN: {product.genericName} · {product.form}</p>
                    <p className='text-sm text-muted-foreground'>{product.manufacturer}</p>
                  </div>
                  <div className='text-left sm:text-right'>
                    <p className='font-semibold'>{product.price.toFixed(2)}</p>
                    <p className='text-xs text-muted-foreground'>Stock {product.stock} · FEFO {product.expiry}</p>
                  </div>
                </div>
              </button>
            ))}
            {results.length === 0 && <p className='py-3 text-sm text-muted-foreground'>No local products match this search.</p>}

            {query.trim().length >= 2 && (
              <div className='space-y-3 border-t pt-4'>
                <div className='flex flex-wrap items-center justify-between gap-2'>
                  <p className='font-medium'>International drug reference</p>
                  <Badge variant='outline'>NLM RxNorm</Badge>
                </div>
                <p className='text-xs text-muted-foreground'>Reference records help identify medicines. They are not sellable stock until linked to a local product with price, inventory, and a valid batch.</p>
                {referenceLoading && <p className='text-sm text-muted-foreground'>Searching the reference catalog…</p>}
                {referenceError && <p className='text-sm text-destructive'>The reference catalog could not be reached. Check the API connection and whether the catalog import has been run.</p>}
                {!referenceLoading && !referenceError && referenceResults.map((item) => (
                  <div key={item.medicinal_product_id} className='rounded-lg border p-3'>
                    <div className='flex flex-wrap items-center gap-2'>
                      <p className='font-medium'>{item.brand_name || [item.inn_name, item.strength].filter(Boolean).join(' ')}</p>
                      <Badge variant='secondary'>{item.product_type === 'brand' ? 'Brand' : 'Generic'}</Badge>
                      <Badge variant='outline'>Reference only</Badge>
                    </div>
                    <p className='mt-1 text-sm text-muted-foreground'>INN: {item.inn_name}{item.strength ? ` · ${item.strength}` : ''}{item.dosage_form ? ` · ${item.dosage_form}` : ''}</p>
                    {item.manufacturer && <p className='text-sm text-muted-foreground'>{item.manufacturer}</p>}
                    {item.regulatory_id && <p className='text-xs text-muted-foreground'>{item.regulatory_id}</p>}
                  </div>
                ))}
                {!referenceLoading && !referenceError && referenceResults.length === 0 && <p className='text-sm text-muted-foreground'>No reference matches. The database may not be populated yet.</p>}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className='h-fit'>
          <CardHeader>
            <div className='flex items-center justify-between'>
              <CardTitle className='flex items-center gap-2'><ShoppingCart className='size-5' /> Current Receipt</CardTitle>
              <span className='text-sm text-muted-foreground'>{cart.reduce((sum, item) => sum + item.quantity, 0)} items</span>
            </div>
          </CardHeader>
          <CardContent className='space-y-4'>
            {cart.length === 0 ? (
              <div className='rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground'>Scan or select a product to start a receipt.</div>
            ) : (
              <div className='space-y-3'>
                {cart.map((item) => (
                  <div key={item.id} className='rounded-lg border p-3'>
                    <div className='flex justify-between gap-3'>
                      <div><p className='font-medium'>{item.name}</p><p className='text-xs text-muted-foreground'>Batch {item.batch} · FEFO {item.expiry}</p></div>
                      <Button variant='ghost' size='icon' onClick={() => setCart((items) => items.filter((x) => x.id !== item.id))}><Trash2 className='size-4' /></Button>
                    </div>
                    <div className='mt-3 flex items-center justify-between'>
                      <div className='flex items-center gap-1'>
                        <Button variant='outline' size='icon' className='size-8' onClick={() => updateQuantity(item.id, -1)}><Minus className='size-3' /></Button>
                        <span className='w-8 text-center text-sm'>{item.quantity}</span>
                        <Button variant='outline' size='icon' className='size-8' onClick={() => updateQuantity(item.id, 1)}><Plus className='size-3' /></Button>
                      </div>
                      <span className='font-medium'>{(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className='rounded-lg bg-muted/50 p-4'>
              <div className='flex items-center gap-2 text-sm text-muted-foreground'><UserRound className='size-4' /> Patient</div>
              <Button variant='outline' className='mt-2 w-full justify-start'>Search patient</Button>
            </div>

            <div className='flex items-center justify-between border-t pt-4 text-lg font-semibold'>
              <span>Total</span><span>{total.toFixed(2)}</span>
            </div>
            <Button className='w-full' size='lg' disabled={!cart.length}>Pay</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
