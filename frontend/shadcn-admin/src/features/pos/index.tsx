import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Search,
  Plus,
  Minus,
  Trash2,
  CreditCard,
  Pill,
  X,
  Receipt,
} from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

type LocalProduct = {
  id: number
  name: string
  sku: string
  dosage_strength: string | null
  dosage_form: string | null
  units_per_pack: number
  manufacturer: string | null
  inn_name: string | null
  gtin: string | null
  barcode: string | null
  price: number
  stock: number
  medicinal_product_id: number | null
  batch_number?: string | null
  expiry_date?: string | null
}
type DrugCatalogResult = {
  medicinal_product_id: number | null
  drug_reference_id: number | null
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
  authorization_country: string | null
  source_record_id?: string | null
  source_name?: string | null
  review_status?: string
  authorization_status?: string | null
  product_class?: string | null
}
type InventoryLot = {
  inventory_id: number
  lot_number: string | null
  expiry_date: string | null
  quantity: number
  reserved_quantity: number
  available_quantity: number
  expiry_date_missing: boolean
}
type CartItem = LocalProduct & { quantity: number }
type PharmacyOption = { id: number; name: string }
type SaleResult = {
  id: number
  receipt_number: string
  status: string
  total: string
  payments: { id: number; method: string; status: string }[]
}
const money = (value: number) =>
  new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)

export function Pos() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LocalProduct[]>([])
  const [lotsByProduct, setLotsByProduct] = useState<
    Record<number, InventoryLot[]>
  >({})
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>(
    []
  )
  const [cart, setCart] = useState<CartItem[]>([])
  const [pharmacyId, setPharmacyId] = useState<number>()
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [receivingOpen, setReceivingOpen] = useState(false)
  const [receivingProductId, setReceivingProductId] = useState('')
  const [receivingLot, setReceivingLot] = useState('')
  const [receivingExpiry, setReceivingExpiry] = useState('')
  const [receivingQuantity, setReceivingQuantity] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<
    'cash' | 'card_terminal' | 'online'
  >('cash')
  const [cashReceived, setCashReceived] = useState('')
  const [processing, setProcessing] = useState(false)
  const [sale, setSale] = useState<SaleResult | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const [searchActive, setSearchActive] = useState(false)
  const idempotencyKey = useRef(crypto.randomUUID())

  const total = useMemo(
    () => cart.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cart]
  )
  const cash = Number(cashReceived) || 0
  const units = cart.reduce((sum, item) => sum + item.quantity, 0)

  useEffect(() => {
    apiFetch<PharmacyOption[]>('/api/v1/pharmacies')
      .then((items) => {
        setPharmacyId(items[0]?.id)
      })
      .catch(() => setNotice('Unable to load pharmacies.'))
  }, [])

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2 || !pharmacyId) return
    let cancelled = false
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const [local, reference] = await Promise.all([
          apiFetch<LocalProduct[]>(
            `/api/v1/pos/products/search?q=${encodeURIComponent(term)}&pharmacy_id=${pharmacyId}&limit=30`
          ),
          apiFetch<DrugCatalogResult[]>(
            `/drug-catalog/search?q=${encodeURIComponent(term)}&limit=50`
          ).catch(() => []),
        ])
        if (!cancelled) {
          setResults(local)
          setReferenceResults(reference)
        }
      } catch {
        if (!cancelled) {
          setResults([])
          setReferenceResults([])
          setNotice('Pharmacy product search failed.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 200)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [query, pharmacyId])

  const formatExpiry = (value?: string | null) =>
    value
      ? new Date(`${value}T00:00:00`).toLocaleDateString('uk-UA')
      : 'Not specified — determined by batch'

  useEffect(() => {
    if (!pharmacyId || cart.length === 0) return
    let cancelled = false
    Promise.all(
      cart.map(async (item) => {
        try {
          const lots = await apiFetch<InventoryLot[]>(
            `/api/v1/pos/products/${item.id}/lots?pharmacy_id=${pharmacyId}`
          )
          return [item.id, lots] as const
        } catch {
          return [item.id, []] as const
        }
      })
    ).then((entries) => {
      if (!cancelled) setLotsByProduct(Object.fromEntries(entries))
    })
    return () => {
      cancelled = true
    }
  }, [cart, pharmacyId])

  const addProduct = (product: LocalProduct) => {
    if (product.stock < 1) {
      setNotice('No available stock.')
      return
    }
    if (cart.length === 0) setLotsByProduct({})
    setResults([])
    setReferenceResults([])
    setLoading(false)
    setCart((items) => {
      const found = items.find((item) => item.id === product.id)
      if (found)
        return items.map((item) =>
          item.id === product.id
            ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) }
            : item
        )
      return [...items, { ...product, quantity: 1 }]
    })
    setNotice('')
    setQuery('')
    setSearchActive(true)
    searchRef.current?.focus()
  }

  const changeQuantity = (id: number, delta: number) =>
    setCart((items) =>
      items.flatMap((item) => {
        if (item.id !== id) return [item]
        const next = Math.min(item.stock, item.quantity + delta)
        return next > 0 ? [{ ...item, quantity: next }] : []
      })
    )

  const receiveStock = async () => {
    const quantity = Number(receivingQuantity)
    if (
      !pharmacyId ||
      !receivingProductId ||
      !receivingLot.trim() ||
      !receivingExpiry ||
      !Number.isInteger(quantity) ||
      quantity <= 0
    ) {
      setNotice(
        'Enter a product, batch number, expiry date, and a positive whole-number quantity.'
      )
      return
    }
    setProcessing(true)
    setNotice('')
    try {
      const received = await apiFetch<{
        lot_quantity: number
        available_quantity: number
        lot_number: string
      }>('/api/v1/pos/inventory/receive', {
        method: 'POST',
        body: JSON.stringify({
          pharmacy_id: pharmacyId,
          product_id: Number(receivingProductId),
          lot_number: receivingLot.trim(),
          expiry_date: `${receivingExpiry}T00:00:00`,
          quantity,
        }),
      })
      setReceivingOpen(false)
      setReceivingLot('')
      setReceivingExpiry('')
      setReceivingQuantity('')
      setNotice(
        `Stock received. Batch ${received.lot_number}: available: ${received.available_quantity} units`
      )
      if (query.trim().length >= 2) {
        const refreshed = await apiFetch<LocalProduct[]>(
          `/api/v1/pos/products/search?q=${encodeURIComponent(query.trim())}&pharmacy_id=${pharmacyId}&limit=30`
        )
        setResults(refreshed)
      }
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : 'Unable to record stock receipt.'
      )
    } finally {
      setProcessing(false)
    }
  }

  const completeSale = async () => {
    if (!pharmacyId || !cart.length || processing) return
    if (paymentMethod === 'cash' && cash < total) {
      setNotice('Cash received is less than the total.')
      return
    }
    setProcessing(true)
    setNotice('')
    try {
      const result = await apiFetch<SaleResult>('/api/v1/pos/checkout', {
        method: 'POST',
        body: JSON.stringify({
          pharmacy_id: pharmacyId,
          idempotency_key: idempotencyKey.current,
          items: cart.map((item) => ({
            product_id: item.id,
            quantity: item.quantity,
          })),
          discount_total: 0,
          payment_method: paymentMethod,
          ...(paymentMethod === 'cash' ? { cash_received: cash } : {}),
        }),
      })
      setSale(result)
      idempotencyKey.current = crypto.randomUUID()
      if (result.status === 'completed') {
        setCart([])
        setLotsByProduct({})
        setCheckoutOpen(false)
        setNotice(`Sale completed. Receipt # ${result.receipt_number}`)
      } else {
        setNotice(
          `Payment is awaiting provider confirmation. Receipt ${result.receipt_number}; stock is reserved.`
        )
      }
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : 'Sale was not confirmed. Check the transaction status before retrying.'
      )
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className='min-h-screen bg-muted/20 p-3 md:p-5'>
      <div className='mx-auto flex min-h-[calc(100vh-2.5rem)] w-full max-w-[1920px] flex-col gap-4'>
        <header className='flex items-center justify-end gap-3 bg-transparent py-2'>
          <Button
            onClick={() => {
              setCart([])
              setLotsByProduct({})
              setResults([])
              setReferenceResults([])
              setLoading(false)
              setSale(null)
              setCheckoutOpen(false)
              setQuery('')
              setSearchActive(true)
              setNotice('New sale. Search is active.')
              window.requestAnimationFrame(() => searchRef.current?.focus())
            }}
          >
            <Plus className='mr-2 size-4' /> Open Sale
          </Button>
          <div className='flex items-center gap-2'>
            <span className='flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground'>
              <Pill className='size-5' />
            </span>
            <h1 className='text-lg font-semibold'>Pharmaviyum POS</h1>
          </div>
        </header>

        {notice && (
          <div
            role='status'
            className='flex items-center justify-between gap-3 rounded-lg border bg-background p-3 text-sm'
          >
            {notice}
            <button
              aria-label='Dismiss notification'
              onClick={() => setNotice('')}
            >
              <X className='size-4' />
            </button>
          </div>
        )}

        {cart.length > 0 && (
          <Card className='min-h-0 flex-1 overflow-y-auto'>
            <CardHeader className='pb-3'>
              <div className='flex items-center justify-between'>
                <CardTitle>Cart</CardTitle>
                <Badge>{units} units</Badge>
              </div>
              <p className='text-sm text-muted-foreground'>
                Review the items and quantities before checkout.
              </p>
            </CardHeader>
            <CardContent className='space-y-3'>
              {cart.map((item) => (
                <div
                  key={item.id}
                  className='flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3'
                >
                  <div className='min-w-0 flex-1'>
                    <p className='font-semibold'>{item.name}</p>
                    <p className='text-xs text-muted-foreground'>
                      {[
                        item.inn_name,
                        item.dosage_strength,
                        item.dosage_form,
                        item.manufacturer,
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    <p className='mt-1 text-sm'>
                      Price: {money(item.price)} · Available: {item.stock} · In
                      cart: {item.quantity} units
                    </p>
                    <div className='mt-2 space-y-1 text-xs text-muted-foreground'>
                      <p className='font-medium text-foreground'>
                        Inventory lots (earliest expiry first):
                      </p>
                      {(lotsByProduct[item.id] || []).length ? (
                        lotsByProduct[item.id].map((lot) => (
                          <p key={lot.inventory_id}>
                            Batch: {lot.lot_number || 'no number'} · Expires:{' '}
                            {formatExpiry(lot.expiry_date)} · Available:{' '}
                            {lot.available_quantity} units
                          </p>
                        ))
                      ) : (
                        <p>
                          No eligible inventory lots found. Check stock
                          receipts.
                        </p>
                      )}
                    </div>
                    <p className='text-xs text-muted-foreground'>
                      Barcode: {item.barcode || item.gtin || 'not specified'}
                    </p>
                  </div>
                  <div className='flex items-center gap-2'>
                    <Button
                      size='icon'
                      variant='outline'
                      aria-label='Decrease quantity'
                      onClick={() => changeQuantity(item.id, -1)}
                    >
                      <Minus className='size-4' />
                    </Button>
                    <span className='w-8 text-center font-semibold'>
                      {item.quantity}
                    </span>
                    <Button
                      size='icon'
                      variant='outline'
                      aria-label='Increase quantity'
                      disabled={item.quantity >= item.stock}
                      onClick={() => changeQuantity(item.id, 1)}
                    >
                      <Plus className='size-4' />
                    </Button>
                    <Button
                      size='icon'
                      variant='ghost'
                      aria-label='Remove item'
                      onClick={() =>
                        setCart((rows) =>
                          rows.filter((row) => row.id !== item.id)
                        )
                      }
                    >
                      <Trash2 className='size-4' />
                    </Button>
                  </div>
                  <strong className='w-28 text-right'>
                    {money(item.price * item.quantity)}
                  </strong>
                </div>
              ))}
              <div className='flex flex-wrap items-center justify-between gap-3 border-t pt-4'>
                <span className='text-lg font-semibold'>
                  Total: {money(total)}
                </span>
                <Button
                  size='lg'
                  onClick={() => {
                    setCashReceived(total.toFixed(2))
                    setCheckoutOpen(true)
                  }}
                >
                  <CreditCard className='mr-2 size-4' /> Proceed to checkout
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {sale?.status === 'completed' && (
          <Card>
            <CardContent className='flex items-center justify-between gap-3 p-4'>
              <div className='flex items-center gap-2'>
                <Receipt className='size-5 text-primary' />
                <div>
                  <p className='font-semibold'>
                    Receipt # {sale.receipt_number}
                  </p>
                  <p className='text-sm text-muted-foreground'>
                    Sale recorded · {money(Number(sale.total))}
                  </p>
                </div>
              </div>
              <Button
                variant='outline'
                onClick={() => {
                  setSale(null)
                  setNotice('New Sale.')
                  searchRef.current?.focus()
                }}
              >
                New Sale
              </Button>
            </CardContent>
          </Card>
        )}

        <section
          aria-label='Medicine search'
          className='flex min-h-[24vh] flex-1 flex-col justify-start py-5'
        >
          <div className='mx-auto w-full max-w-3xl'>
            <form
              aria-label='Medicine search'
              onSubmit={(e) => {
                e.preventDefault()
                if (results.length === 1) addProduct(results[0])
              }}
              className='relative w-full'
            >
              <Search
                aria-hidden='true'
                className='pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-muted-foreground'
              />
              <Input
                ref={searchRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value)
                  setResults([])
                  setReferenceResults([])
                  setLoading(false)
                }}
                placeholder='Search medicines by name, INN, brand, strength or barcode…'
                className={`h-12 w-full pr-4 pl-12 text-base transition-shadow ${searchActive ? 'ring-2 ring-primary ring-offset-2' : ''}`}
                onFocus={() => setSearchActive(true)}
              />{' '}
            </form>
            {loading && (
              <p className='py-4 text-center text-sm text-muted-foreground'>
                Searching medicines…
              </p>
            )}
            {!loading && query.trim().length >= 2 && results.length === 0 && (
              <p className='py-5 text-center text-sm text-muted-foreground'>
                No matches in this pharmacy's inventory.
              </p>
            )}
            {query.trim().length >= 2 &&
              results.map((product) => (
                <div
                  key={product.id}
                  className='flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3'
                >
                  <div className='min-w-0 flex-1'>
                    <p className='font-semibold'>{product.name}</p>
                    <p className='text-xs text-muted-foreground'>
                      Brand / manufacturer:{' '}
                      {product.manufacturer || 'not specified'} · INN:{' '}
                      {product.inn_name || 'not specified'}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      {[product.dosage_strength, product.dosage_form]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    <p className='mt-1 text-xs text-muted-foreground'>
                      SKU: {product.sku} · Available: {product.stock} · Price:{' '}
                      {money(product.price)}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      Barcode:{' '}
                      {product.barcode || product.gtin || 'not specified'}
                    </p>
                  </div>
                  <Button
                    onClick={() => addProduct(product)}
                    disabled={product.stock < 1}
                  >
                    <Plus className='mr-1 size-4' /> Add
                  </Button>
                </div>
              ))}
            {query.trim().length >= 2 && referenceResults.length > 0 && (
              <div className='space-y-2 border-t pt-3'>
                <p className='text-sm font-semibold'>
                  International drug reference — information only
                </p>
                {referenceResults.map((item, index) => (
                  <div
                    key={
                      item.source_record_id ??
                      item.medicinal_product_id ??
                      index
                    }
                    className='rounded-lg border border-dashed p-3'
                  >
                    <p className='font-medium'>
                      {item.brand_name || item.inn_name}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      Brand: {item.brand_name || 'not specified'} ·
                      Manufacturer: {item.manufacturer || 'not specified'}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      {[
                        item.inn_name,
                        item.strength,
                        item.dosage_form,
                        item.authorization_country,
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      Barcode / GTIN: {item.gtin || 'not available in source'} ·
                      Stock and expiry are available only after a pharmacy batch
                      is recorded
                    </p>
                    <Badge variant='outline' className='mt-2'>
                      Reference record — not a pharmacy product
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>

      {receivingOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'>
          <section
            role='dialog'
            aria-modal='true'
            aria-labelledby='receiving-title'
            className='w-full max-w-lg space-y-4 rounded-xl border bg-background p-5 shadow-xl'
          >
            <div className='flex items-center justify-between'>
              <h2 id='receiving-title' className='text-xl font-bold'>
                Receive Stock
              </h2>
              <Button
                size='icon'
                variant='ghost'
                onClick={() => setReceivingOpen(false)}
                aria-label='Close'
              >
                <X />
              </Button>
            </div>
            <p className='text-sm text-muted-foreground'>
              The receipt will update this pharmacy's inventory and make the
              batch available to POS with expiry controls.
            </p>
            <label className='block text-sm font-medium'>
              Find product
              <Input
                className='mt-2 h-11'
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Name, INN, SKU or barcode'
              />
            </label>
            <div className='max-h-36 space-y-1 overflow-y-auto rounded-md border p-2'>
              {results.map((product) => (
                <button
                  type='button'
                  key={product.id}
                  onClick={() => setReceivingProductId(String(product.id))}
                  className={`flex w-full items-center justify-between rounded-md p-2 text-left text-sm hover:bg-muted ${receivingProductId === String(product.id) ? 'bg-primary/10 outline outline-1 outline-primary' : ''}`}
                >
                  <span>
                    {product.name}
                    <span className='block text-xs text-muted-foreground'>
                      {product.sku} ·{' '}
                      {product.manufacturer || 'manufacturer not specified'}
                    </span>
                  </span>
                  <span>{money(product.price)}</span>
                </button>
              ))}
              {query.trim().length >= 2 && results.length === 0 && (
                <p className='p-2 text-xs text-muted-foreground'>
                  Product not found in local inventory. Add it to the pharmacy
                  assortment first.
                </p>
              )}
            </div>
            <label className='block text-sm font-medium'>
              Batch / lot number
              <Input
                className='mt-2 h-11'
                value={receivingLot}
                onChange={(e) => setReceivingLot(e.target.value)}
                maxLength={100}
              />
            </label>
            <label className='block text-sm font-medium'>
              Expiry date
              <Input
                className='mt-2 h-11'
                type='date'
                min={new Date().toISOString().slice(0, 10)}
                value={receivingExpiry}
                onChange={(e) => setReceivingExpiry(e.target.value)}
              />
            </label>
            <label className='block text-sm font-medium'>
              Received quantity
              <Input
                className='mt-2 h-11'
                type='number'
                min='1'
                step='1'
                value={receivingQuantity}
                onChange={(e) => setReceivingQuantity(e.target.value)}
              />
            </label>
            <div className='flex gap-2'>
              <Button
                className='flex-1'
                disabled={
                  processing ||
                  !receivingProductId ||
                  !receivingLot.trim() ||
                  !receivingExpiry ||
                  Number(receivingQuantity) <= 0
                }
                onClick={() => void receiveStock()}
              >
                {processing ? 'Saving…' : 'Receive stock'}
              </Button>
              <Button
                variant='outline'
                onClick={() => setReceivingOpen(false)}
                disabled={processing}
              >
                Cancel
              </Button>
            </div>
          </section>
        </div>
      )}

      {checkoutOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'>
          <section
            role='dialog'
            aria-modal='true'
            aria-labelledby='checkout-title'
            className='w-full max-w-md space-y-4 rounded-xl border bg-background p-5 shadow-xl'
          >
            <div className='flex items-center justify-between'>
              <h2 id='checkout-title' className='text-xl font-bold'>
                Payment and checkout
              </h2>
              <Button
                size='icon'
                variant='ghost'
                onClick={() => setCheckoutOpen(false)}
                aria-label='Close'
              >
                <X />
              </Button>
            </div>
            <div className='rounded-lg border bg-background p-4'>
              <div className='mb-3 flex items-center justify-between'>
                <p className='font-semibold'>Receipt preview</p>
                <span className='text-xs text-muted-foreground'>UNPAID</span>
              </div>
              <div className='space-y-2 border-y border-dashed py-3 text-sm'>
                {cart.map((item) => (
                  <div key={item.id} className='flex justify-between gap-3'>
                    <div className='min-w-0'>
                      <p className='font-medium'>{item.name}</p>
                      <p className='text-xs text-muted-foreground'>
                        {item.quantity} × {money(item.price)}
                      </p>
                    </div>
                    <strong className='shrink-0'>
                      {money(item.price * item.quantity)}
                    </strong>
                  </div>
                ))}
              </div>
              <div className='flex justify-between pt-3 text-sm'>
                <span>Quantity</span>
                <span>{units} units</span>
              </div>
              <div className='mt-2 flex justify-between text-lg font-bold'>
                <span>TOTAL</span>
                <span>{money(total)}</span>
              </div>
              <p className='mt-2 text-xs text-muted-foreground'>
                This is a draft receipt. The sale and stock deduction are
                recorded only after payment is confirmed.
              </p>
            </div>
            <label className='block text-sm font-medium'>
              Payment method
              <select
                className='mt-2 h-11 w-full rounded-md border bg-background px-3'
                value={paymentMethod}
                onChange={(e) =>
                  setPaymentMethod(e.target.value as typeof paymentMethod)
                }
              >
                <option value='cash'>Cash</option>
                <option value='card_terminal'>Card terminal</option>
                <option value='online'>Online payment</option>
              </select>
            </label>
            {paymentMethod === 'cash' ? (
              <label className='block text-sm font-medium'>
                Cash received
                <Input
                  className='mt-2 h-11'
                  type='number'
                  min='0'
                  step='0.01'
                  value={cashReceived}
                  onChange={(e) => setCashReceived(e.target.value)}
                />
                <span className='mt-2 block text-sm text-muted-foreground'>
                  Change: {money(Math.max(0, cash - total))}
                </span>
              </label>
            ) : (
              <p className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm'>
                Card or online payment completes only after provider
                confirmation. Until then, the sale remains pending and stock is
                reserved.
              </p>
            )}
            <Button
              className='w-full'
              size='lg'
              disabled={
                processing ||
                !pharmacyId ||
                (paymentMethod === 'cash' && cash < total)
              }
              onClick={() => void completeSale()}
            >
              {processing
                ? 'Processing…'
                : paymentMethod === 'cash'
                  ? 'Confirm payment & issue receipt'
                  : 'Create payment'}
            </Button>
            <Button
              variant='outline'
              className='w-full'
              onClick={() => setCheckoutOpen(false)}
              disabled={processing}
            >
              Back to cart
            </Button>
          </section>
        </div>
      )}
    </div>
  )
}
