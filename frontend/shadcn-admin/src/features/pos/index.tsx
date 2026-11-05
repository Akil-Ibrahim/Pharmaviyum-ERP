import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import {
  Barcode, Check, CreditCard, Minus, Plus, Search, ShoppingCart,
  Tag, Trash2, UserRound, X, ScanLine, Keyboard, PackageSearch,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type LocalProduct = {
  id: number; name: string; sku: string; dosage_strength: string | null
  dosage_form: string | null; units_per_pack: number; manufacturer: string | null
  inn_name: string | null; gtin: string | null; barcode: string | null
  price: number; stock: number; medicinal_product_id: number | null
}
type DrugCatalogResult = {
  medicinal_product_id: number; drug_reference_id: number; inn_name: string
  atc_code: string | null; ingredient_names: string[]; brand_name: string | null
  product_type: string; manufacturer: string | null; strength: string | null
  dosage_form: string | null; route: string | null; package_description: string | null
  gtin: string | null; regulatory_id: string | null
}
type CartItem = LocalProduct & { quantity: number }

const money = (value: number) =>
  new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'UAH' }).format(value)

export function Pos() {
  const [query, setQuery] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [localResults, setLocalResults] = useState<LocalProduct[]>([])
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>([])
  const [loading, setLoading] = useState(false)
  const [referenceLoading, setReferenceLoading] = useState(false)
  const [localError, setLocalError] = useState(false)
  const [referenceError, setReferenceError] = useState(false)
  const [discount, setDiscount] = useState('0')
  const [cashReceived, setCashReceived] = useState('')
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [customer, setCustomer] = useState('')
  const [notice, setNotice] = useState('')
  const [selectedForm, setSelectedForm] = useState('all')
  const [stockFilter, setStockFilter] = useState<'all' | 'available' | 'low'>('all')
  const searchRef = useRef<HTMLInputElement>(null)

  const discountPercent = Math.min(100, Math.max(0, Number(discount) || 0))
  const subtotal = useMemo(() => cart.reduce((sum, item) => sum + item.price * item.quantity, 0), [cart])
  const discountAmount = subtotal * discountPercent / 100
  const total = subtotal - discountAmount
  const quantity = cart.reduce((sum, item) => sum + item.quantity, 0)
  const cash = Number(cashReceived) || 0
  const availableForms = useMemo(
    () => Array.from(new Set(localResults.map(item => item.dosage_form?.trim()).filter((form): form is string => Boolean(form)))).sort((a, b) => a.localeCompare(b)),
    [localResults],
  )
  const visibleLocalResults = useMemo(() => localResults.filter(product => {
    const matchesForm = selectedForm === 'all' || product.dosage_form === selectedForm
    const matchesStock = stockFilter === 'all' || (stockFilter === 'available' ? product.stock > 0 : product.stock > 0 && product.stock <= 5)
    return matchesForm && matchesStock
  }), [localResults, selectedForm, stockFilter])

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) {
      setLocalResults([])
      setReferenceResults([])
      setLoading(false)
      setReferenceLoading(false)
      return
    }
    let cancelled = false
    const timer = setTimeout(() => {
      if (cancelled) return
      setLoading(true)
      setReferenceLoading(true)
      setLocalError(false)
      setReferenceError(false)
      apiFetch<LocalProduct[]>(`/products/search?q=${encodeURIComponent(term)}&limit=20`)
        .then(items => { if (!cancelled) setLocalResults(items) })
        .catch(() => { if (!cancelled) { setLocalResults([]); setLocalError(true) } })
        .finally(() => { if (!cancelled) setLoading(false) })
      apiFetch<DrugCatalogResult[]>(`/drug-catalog/search?q=${encodeURIComponent(term)}&limit=8`)
        .then(items => { if (!cancelled) setReferenceResults(items) })
        .catch(() => { if (!cancelled) { setReferenceResults([]); setReferenceError(true) } })
        .finally(() => { if (!cancelled) setReferenceLoading(false) })
    }, 180)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [query])

  const resetSale = () => {
    setCart([])
    setQuery('')
    setDiscount('0')
    setCustomer('')
    setCashReceived('')
    setSelectedForm('all')
    setStockFilter('all')
    setPaymentOpen(false)
    setNotice('New sale is ready.')
    searchRef.current?.focus()
  }

  const addToCart = (product: LocalProduct) => {
    if (product.stock < 1) {
      setNotice('This product is out of stock.')
      return
    }
    setNotice('')
    setCart(items => {
      const existing = items.find(item => item.id === product.id)
      if (existing) return items.map(item =>
        item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item
      )
      return [...items, { ...product, quantity: 1 }]
    })
    setQuery('')
    searchRef.current?.focus()
  }

  const updateQuantity = (id: number, delta: number) => setCart(items => items.flatMap(item => {
    if (item.id !== id) return [item]
    const next = item.quantity + delta
    return next > 0 ? [{ ...item, quantity: Math.min(next, item.stock) }] : []
  }))

  const scanSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const term = query.trim()
    if (!term) return
    const findExact = (items: LocalProduct[]) => items.find(item =>
      item.barcode === term || item.gtin === term || item.sku.toLowerCase() === term.toLowerCase()
    )
    const existingMatch = findExact(localResults)
    if (existingMatch) {
      addToCart(existingMatch)
      return
    }
    setLoading(true)
    try {
      const freshResults = await apiFetch<LocalProduct[]>(`/products/search?q=${encodeURIComponent(term)}&limit=20`)
      setLocalResults(freshResults)
      const exactMatch = findExact(freshResults)
      if (exactMatch) addToCart(exactMatch)
      else setNotice('No exact barcode or SKU match. Review the results and confirm local stock availability.')
    } catch {
      setNotice('The pharmacy catalog could not be searched. Check the connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const beginPayment = () => {
    if (!cart.length) return
    setPaymentOpen(true)
    setCashReceived(total.toFixed(2))
  }

  const closePaymentReview = () => {
    setNotice('Payment review closed. No sale was recorded.')
    setPaymentOpen(false)
  }

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if (event.key === 'F2') {
        event.preventDefault()
        searchRef.current?.focus()
        searchRef.current?.select()
      } else if (event.key === 'Escape') {
        if (paymentOpen) setPaymentOpen(false)
        else if (query) setQuery('')
      } else if (event.key === 'F4' && cart.length > 0) {
        event.preventDefault()
        beginPayment()
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [cart.length, paymentOpen, query, total])

  return (
    <div className='pharmacy-pos min-h-full space-y-4 bg-muted/20 p-3 md:p-5'>
      <header className='flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-background px-4 py-3 shadow-sm'>
        <div className='flex min-w-0 items-center gap-3'>
          <span className='flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground'>
            <ShoppingCart className='size-5' />
          </span>
          <div className='min-w-0'>
            <h1 className='text-xl font-bold tracking-tight'>Pharmacy POS</h1>
            <p className='text-xs text-muted-foreground'>Point of sale · Counter workspace</p>
          </div>
        </div>
        <div className='flex flex-wrap items-center gap-2'>
          <Badge variant='outline' className='px-3 py-2'>Counter workspace</Badge>
          <Button variant='outline' onClick={resetSale}>
            <Plus className='mr-2 size-4' /> New sale
          </Button>
        </div>
      </header>

      {notice && (
        <div role='status' className='flex items-start justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2.5 text-sm'>
          <span>{notice}</span>
          <button aria-label='Dismiss notification' onClick={() => setNotice('')}><X className='size-4' /></button>
        </div>
      )}

      <div className='grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_390px] 2xl:grid-cols-[minmax(0,1fr)_420px]'>
        <main className='grid min-w-0 gap-4 lg:grid-cols-[176px_minmax(0,1fr)]'>
          <Card className='overflow-hidden border-primary/20 shadow-sm lg:col-span-2'>
            <CardHeader className='bg-primary/[0.045] pb-3'>
              <div className='flex flex-wrap items-center justify-between gap-2'>
                <div>
                  <CardTitle className='flex items-center gap-2 text-base'><PackageSearch className='size-5 text-primary' /> Find a medicine</CardTitle>
                  <p className='mt-1 text-sm text-muted-foreground'>Search by product name, INN, brand, manufacturer, SKU or barcode.</p>
                </div>
                <Badge variant='outline'>F2 · Search</Badge>
              </div>
            </CardHeader>
            <CardContent className='space-y-2 pt-4'>
              <form onSubmit={scanSubmit} className='flex flex-col gap-2 sm:flex-row'>
                <div className='relative min-w-0 flex-1'>
                  <Search className='pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-muted-foreground' />
                  <Input
                    ref={searchRef}
                    value={query}
                    onChange={event => setQuery(event.target.value)}
                    placeholder='Scan barcode or type a medicine name…'
                    className='h-12 pl-11 text-base'
                    autoComplete='off'
                    aria-label='Search medicines by name or barcode'
                  />
                </div>
                <Button type='submit' className='h-12 px-5'>
                  <ScanLine className='mr-2 size-4' /> Search / scan
                </Button>
              </form>
              <div className='flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground'>
                <span className='flex items-center gap-1.5'><Barcode className='size-3.5' /> USB barcode scanners work as keyboard input.</span>
                <span className='flex items-center gap-1.5'><Keyboard className='size-3.5' /> Enter: add exact barcode · F4: payment review · Esc: clear</span>
              </div>
            </CardContent>
          </Card>

          <Card className='h-fit shadow-sm'>
            <CardHeader className='pb-2'>
              <CardTitle className='text-sm'>Browse catalog</CardTitle>
              <p className='text-xs text-muted-foreground'>Filter current search</p>
            </CardHeader>
            <CardContent className='space-y-1 px-2 pb-3'>
              <Button variant={selectedForm === 'all' ? 'secondary' : 'ghost'} className='w-full justify-start' size='sm' onClick={() => setSelectedForm('all')}>
                <PackageSearch className='mr-2 size-4' /> All products
                <span className='ml-auto text-xs text-muted-foreground'>{localResults.length}</span>
              </Button>
              {availableForms.map(form => (
                <Button key={form} variant={selectedForm === form ? 'secondary' : 'ghost'} className='w-full justify-start' size='sm' onClick={() => setSelectedForm(form)}>
                  <span className='mr-2 size-1.5 rounded-full bg-muted-foreground/60' /> <span className='truncate'>{form}</span>
                </Button>
              ))}
              <div className='my-2 border-t pt-2'>
                <p className='px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground'>Availability</p>
                <Button variant={stockFilter === 'all' ? 'secondary' : 'ghost'} className='w-full justify-start' size='sm' onClick={() => setStockFilter('all')}>All stock</Button>
                <Button variant={stockFilter === 'available' ? 'secondary' : 'ghost'} className='w-full justify-start' size='sm' onClick={() => setStockFilter('available')}>In stock</Button>
                <Button variant={stockFilter === 'low' ? 'secondary' : 'ghost'} className='w-full justify-start' size='sm' onClick={() => setStockFilter('low')}>Low stock (1–5)</Button>
              </div>
              <p className='px-2 pt-1 text-[11px] text-muted-foreground'>Categories are derived from product dosage forms returned by the catalog.</p>
            </CardContent>
          </Card>

          <Card className='overflow-hidden shadow-sm'>
            <CardHeader className='border-b bg-background py-3'>
              <div className='flex flex-wrap items-center justify-between gap-2'>
                <div>
                  <CardTitle className='text-base'>Search results</CardTitle>
                  <p className='mt-1 text-xs text-muted-foreground'>Only pharmacy products with local pricing and stock can be added to the sale.</p>
                </div>
                <Badge variant='secondary'>{visibleLocalResults.length} products</Badge>
              </div>
            </CardHeader>
            <CardContent className='p-0'>
              {loading && <p className='px-4 py-10 text-center text-sm text-muted-foreground'>Searching pharmacy catalog…</p>}
              {localError && <p className='m-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive'>Unable to load pharmacy products. Check the API connection and access permissions.</p>}
              {!loading && !localError && query.trim().length >= 2 && localResults.length === 0 && (
                <div className='px-4 py-10 text-center'>
                  <PackageSearch className='mx-auto mb-2 size-7 text-muted-foreground' />
                  <p className='text-sm font-medium'>No pharmacy products found</p>
                  <p className='mt-1 text-xs text-muted-foreground'>Try another name, INN, SKU or barcode.</p>
                </div>
              )}
              {query.trim().length >= 2 && !loading && localResults.length > 0 && visibleLocalResults.length === 0 && <p className='px-4 py-10 text-center text-sm text-muted-foreground'>No products match the selected filters.</p>}
              {query.trim().length < 2 && (
                <div className='px-4 py-12 text-center'>
                  <Search className='mx-auto mb-3 size-8 text-muted-foreground/60' />
                  <p className='text-sm font-medium'>Ready to search</p>
                  <p className='mt-1 text-xs text-muted-foreground'>Scan a product barcode or enter at least two characters.</p>
                </div>
              )}
              {visibleLocalResults.length > 0 && (
                <div className='overflow-x-auto'>
                  <table className='w-full min-w-[680px] text-sm'>
                    <thead className='bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground'>
                      <tr>
                        <th className='px-4 py-3 font-medium'>Product / manufacturer</th>
                        <th className='px-3 py-3 font-medium'>SKU / barcode</th>
                        <th className='px-3 py-3 text-right font-medium'>In stock</th>
                        <th className='px-3 py-3 text-right font-medium'>Unit price</th>
                        <th className='px-4 py-3 text-right font-medium'>Action</th>
                      </tr>
                    </thead>
                    <tbody className='divide-y'>
                      {visibleLocalResults.map(product => (
                        <tr key={product.id} className='bg-background transition-colors hover:bg-muted/30'>
                          <td className='px-4 py-3'>
                            <p className='font-semibold'>{product.name}</p>
                            <p className='mt-1 text-xs text-muted-foreground'>
                              {[product.inn_name, product.dosage_strength, product.dosage_form, product.manufacturer].filter(Boolean).join(' · ') || 'No additional details'}
                            </p>
                          </td>
                          <td className='px-3 py-3 text-xs text-muted-foreground'>
                            <p>{product.sku}</p>
                            {(product.barcode || product.gtin) && <p className='mt-1'>{product.barcode || product.gtin}</p>}
                          </td>
                          <td className='px-3 py-3 text-right'>
                            <span className={product.stock < 1 ? 'font-semibold text-destructive' : product.stock <= 5 ? 'font-semibold text-amber-600' : 'font-medium text-emerald-600'}>
                              {product.stock}
                            </span>
                          </td>
                          <td className='px-3 py-3 text-right font-semibold tabular-nums'>{money(product.price)}</td>
                          <td className='px-4 py-3 text-right'>
                            <Button size='sm' onClick={() => addToCart(product)} disabled={product.stock < 1}>
                              <Plus className='mr-1 size-4' /> Add
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {query.trim().length >= 2 && (
            <Card className='shadow-sm'>
              <CardHeader className='pb-2'>
                <div className='flex flex-wrap items-center justify-between gap-2'>
                  <div>
                    <CardTitle className='text-sm'>International medicine reference</CardTitle>
                    <p className='mt-1 text-xs text-muted-foreground'>Reference information only — not a pharmacy stock item.</p>
                  </div>
                  <Badge variant='outline'>Reference catalog</Badge>
                </div>
              </CardHeader>
              <CardContent className='space-y-2'>
                {referenceLoading && <p className='text-sm text-muted-foreground'>Searching reference catalog…</p>}
                {referenceError && <p className='text-sm text-destructive'>The reference catalog is unavailable.</p>}
                {!referenceLoading && !referenceError && referenceResults.length === 0 && <p className='text-xs text-muted-foreground'>No reference matches.</p>}
                {referenceResults.map(item => (
                  <div key={item.medicinal_product_id} className='flex flex-col justify-between gap-2 rounded-lg border p-3 sm:flex-row sm:items-center'>
                    <div className='min-w-0'>
                      <p className='font-medium'>{item.brand_name || [item.inn_name, item.strength].filter(Boolean).join(' ')}</p>
                      <p className='mt-1 text-xs text-muted-foreground'>{[item.inn_name, item.strength, item.dosage_form, item.manufacturer].filter(Boolean).join(' · ')}</p>
                    </div>
                    <Badge variant='outline' className='w-fit shrink-0'>Not for checkout</Badge>
                  </div>
                ))}
                <p className='text-xs text-muted-foreground'>A reference record does not confirm local market authorization, pharmacy pricing or stock availability.</p>
              </CardContent>
            </Card>
          )}
        </main>

        <aside className='space-y-4 xl:sticky xl:top-4'>
          <Card className='overflow-hidden border-primary/20 shadow-sm'>
            <CardHeader className='bg-primary/[0.045] pb-3'>
              <div className='flex items-center justify-between gap-2'>
                <CardTitle className='flex items-center gap-2 text-base'><ShoppingCart className='size-5 text-primary' /> Current sale</CardTitle>
                <Badge>{quantity} units</Badge>
              </div>
              <p className='text-xs text-muted-foreground'>Draft receipt · Not submitted</p>
            </CardHeader>
            <CardContent className='space-y-4 pt-4'>
              {cart.length === 0 ? (
                <div className='rounded-xl border border-dashed px-4 py-9 text-center'>
                  <ShoppingCart className='mx-auto mb-2 size-7 text-muted-foreground/60' />
                  <p className='text-sm font-medium'>Your sale is empty</p>
                  <p className='mt-1 text-xs text-muted-foreground'>Add a product from the search results.</p>
                </div>
              ) : (
                <div className='max-h-[340px] space-y-3 overflow-y-auto pr-1'>
                  {cart.map(item => (
                    <div key={item.id} className='rounded-lg border p-3'>
                      <div className='flex items-start justify-between gap-2'>
                        <div className='min-w-0'>
                          <p className='text-sm font-semibold leading-snug'>{item.name}</p>
                          <p className='mt-1 text-xs text-muted-foreground'>{money(item.price)} / unit · Stock {item.stock}</p>
                        </div>
                        <Button variant='ghost' size='icon' className='size-7 shrink-0 text-muted-foreground hover:text-destructive' aria-label={`Remove ${item.name}`} onClick={() => setCart(items => items.filter(row => row.id !== item.id))}>
                          <Trash2 className='size-4' />
                        </Button>
                      </div>
                      <div className='mt-3 flex items-center justify-between gap-3'>
                        <div className='flex items-center gap-2'>
                          <Button variant='outline' size='icon' className='size-8' aria-label='Decrease quantity' onClick={() => updateQuantity(item.id, -1)}><Minus className='size-3' /></Button>
                          <span className='w-6 text-center text-sm font-semibold tabular-nums'>{item.quantity}</span>
                          <Button variant='outline' size='icon' className='size-8' aria-label='Increase quantity' disabled={item.quantity >= item.stock} onClick={() => updateQuantity(item.id, 1)}><Plus className='size-3' /></Button>
                        </div>
                        <span className='font-semibold tabular-nums'>{money(item.price * item.quantity)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className='rounded-xl bg-muted/40 p-3'>
                <div className='mb-2 flex items-center gap-2 text-sm font-medium'><UserRound className='size-4 text-muted-foreground' /> Customer / loyalty</div>
                <Input value={customer} onChange={event => setCustomer(event.target.value)} placeholder='Phone number or loyalty card' />
                <p className='mt-1 text-xs text-muted-foreground'>Customer lookup and rewards are not connected yet.</p>
              </div>

              <div className='rounded-xl border p-3'>
                <div className='mb-2 flex items-center gap-2 text-sm font-medium'><Tag className='size-4 text-muted-foreground' /> Receipt discount</div>
                <div className='flex items-center gap-2'>
                  <Input type='number' min='0' max='100' step='0.5' value={discount} onChange={event => setDiscount(event.target.value)} aria-label='Discount percentage' />
                  <span className='text-sm text-muted-foreground'>%</span>
                  <div className='flex gap-1'>
                    {[0, 5, 10].map(value => <Button key={value} variant={discountPercent === value ? 'default' : 'outline'} size='sm' onClick={() => setDiscount(String(value))}>{value}%</Button>)}
                  </div>
                </div>
              </div>

              <div className='space-y-2 border-t pt-4 text-sm'>
                <div className='flex justify-between text-muted-foreground'><span>Subtotal</span><span className='tabular-nums'>{money(subtotal)}</span></div>
                <div className='flex justify-between text-rose-600'><span>Discount</span><span className='tabular-nums'>−{money(discountAmount)}</span></div>
                <div className='flex items-end justify-between gap-3 rounded-lg bg-primary/[0.06] p-3'>
                  <span className='font-semibold'>Total due</span>
                  <span className='text-2xl font-bold tracking-tight tabular-nums'>{money(total)}</span>
                </div>
              </div>

              <Button className='h-12 w-full text-base' size='lg' onClick={beginPayment} disabled={!cart.length}>
                <CreditCard className='mr-2 size-5' /> Review payment
              </Button>
              <Button variant='outline' className='w-full' onClick={resetSale} disabled={!cart.length && !customer && discountPercent === 0}>
                <X className='mr-2 size-4' /> Clear sale
              </Button>
              <p className='text-xs leading-relaxed text-muted-foreground'>Checkout is in review-only mode. A completed sale requires an atomic backend transaction for receipt lines, payment and stock allocation.</p>
            </CardContent>
          </Card>

          <div className='grid grid-cols-3 gap-2'>
            {[
              { label: 'Items', value: String(cart.length), tone: 'bg-sky-500/10 text-sky-700' },
              { label: 'Units', value: String(quantity), tone: 'bg-emerald-500/10 text-emerald-700' },
              { label: 'Discount', value: `${discountPercent}%`, tone: 'bg-rose-500/10 text-rose-700' },
            ].map(metric => (
              <div key={metric.label} className='rounded-xl border bg-background p-3'>
                <div className={`mb-2 flex size-8 items-center justify-center rounded-lg ${metric.tone}`}><Check className='size-4' /></div>
                <p className='text-lg font-bold tabular-nums'>{metric.value}</p>
                <p className='text-xs text-muted-foreground'>{metric.label}</p>
              </div>
            ))}
          </div>
        </aside>
      </div>

      {paymentOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4' role='presentation' onMouseDown={event => { if (event.target === event.currentTarget) setPaymentOpen(false) }}>
          <section role='dialog' aria-modal='true' aria-labelledby='payment-title' className='w-full max-w-md rounded-2xl border bg-background p-5 shadow-2xl'>
            <div className='mb-4 flex items-center justify-between'>
              <div>
                <h2 id='payment-title' className='text-xl font-bold'>Payment review</h2>
                <p className='text-sm text-muted-foreground'>Verify the amount received.</p>
              </div>
              <Button variant='ghost' size='icon' onClick={() => setPaymentOpen(false)} aria-label='Close payment review'><X className='size-4' /></Button>
            </div>
            <div className='rounded-xl bg-primary/5 p-4'>
              <p className='text-sm text-muted-foreground'>Total due</p>
              <p className='text-3xl font-bold tabular-nums'>{money(total)}</p>
            </div>
            <label className='mt-4 block text-sm font-medium' htmlFor='cash-received'>Cash received (₴)</label>
            <Input id='cash-received' type='number' min='0' step='0.01' value={cashReceived} onChange={event => setCashReceived(event.target.value)} className='mt-2 h-11' />
            <div className='mt-3 flex justify-between rounded-lg border p-3 text-sm'>
              <span className='text-muted-foreground'>Change due</span>
              <strong className={cash < total ? 'text-destructive' : 'text-emerald-600'}>{money(Math.max(0, cash - total))}</strong>
            </div>
            <div className='mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm'>
              Sale completion is disabled. The backend must atomically persist receipt lines, payment and stock movements before checkout can be enabled.
            </div>
            <Button className='mt-4 w-full' variant='outline' onClick={closePaymentReview}>Close review — no sale recorded</Button>
          </section>
        </div>
      )}
    </div>
  )
}
