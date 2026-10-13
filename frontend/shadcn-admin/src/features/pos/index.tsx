import { useEffect, useMemo, useState } from 'react'
import { Barcode, Minus, Plus, Search, ShoppingCart, Trash2, UserRound } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

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

type CartItem = LocalProduct & { quantity: number }

export function Pos() {
  const [query, setQuery] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [localResults, setLocalResults] = useState<LocalProduct[]>([])
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>([])
  const [loading, setLoading] = useState(false)
  const [referenceLoading, setReferenceLoading] = useState(false)
  const [localError, setLocalError] = useState(false)
  const [referenceError, setReferenceError] = useState(false)

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) {
      setLocalResults([])
      setReferenceResults([])
      setLoading(false)
      setReferenceLoading(false)
      setLocalError(false)
      setReferenceError(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setReferenceLoading(true)
    setLocalError(false)
    setReferenceError(false)

    apiFetch<LocalProduct[]>(
      `/api/v1/products/search?q=${encodeURIComponent(term)}&limit=20`,
    )
      .then((items) => {
        if (!cancelled) setLocalResults(items)
      })
      .catch(() => {
        if (!cancelled) {
          setLocalResults([])
          setLocalError(true)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

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

  const addToCart = (product: LocalProduct) => {
    setCart((items) => {
      const existing = items.find((item) => item.id === product.id)
      if (existing) {
        return items.map((item) =>
          item.id === product.id
            ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) }
            : item,
        )
      }
      if (product.stock < 1) return items
      return [...items, { ...product, quantity: 1 }]
    })
  }

  const updateQuantity = (id: number, delta: number) => {
    setCart((items) =>
      items.flatMap((item) => {
        if (item.id !== id) return [item]
        const quantity = item.quantity + delta
        return quantity > 0
          ? [{ ...item, quantity: Math.min(quantity, item.stock) }]
          : []
      }),
    )
  }

  const total = useMemo(
    () => cart.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cart],
  )

  return (
    <div className='space-y-6 p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>POS</h1>
          <p className='text-muted-foreground'>
            Find pharmacy stock or look up a medicine in the international reference.
          </p>
        </div>
        <Badge variant='outline' className='w-fit gap-2 px-3 py-1.5'>
          <span className='size-2 rounded-full bg-emerald-500' /> Product lookup
        </Badge>
      </div>

      <div className='grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]'>
        <Card>
          <CardHeader className='space-y-4'>
            <div className='flex items-center justify-between gap-3'>
              <CardTitle>Search medicines</CardTitle>
              <Button variant='outline' size='sm' disabled>
                <Barcode className='mr-2 size-4' /> Scan
              </Button>
            </div>
            <div className='relative'>
              <Search className='absolute left-3 top-3 size-4 text-muted-foreground' />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder='Name, INN, brand, manufacturer, barcode or SKU…'
                className='pl-9'
                aria-label='Search local and international medicines'
              />
            </div>
            <p className='text-xs text-muted-foreground'>
              Enter at least two characters. Reference medicines are not automatically added to pharmacy stock.
            </p>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex items-center justify-between gap-2'>
              <p className='font-medium'>Available pharmacy products</p>
              <Badge variant='outline'>Local inventory</Badge>
            </div>
            {loading && <p className='text-sm text-muted-foreground'>Searching local products…</p>}
            {localError && (
              <p className='text-sm text-destructive'>
                Local product search failed. Check the API connection and your access.
              </p>
            )}
            {!loading && !localError && query.trim().length >= 2 && localResults.length === 0 && (
              <p className='text-sm text-muted-foreground'>No matching sellable products in the local catalog.</p>
            )}
            {localResults.map((product) => (
              <div key={product.id} className='rounded-lg border p-4'>
                <div className='flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between'>
                  <div className='min-w-0'>
                    <div className='flex flex-wrap items-center gap-2'>
                      <p className='font-semibold'>{product.name}</p>
                      {product.medicinal_product_id && <Badge variant='secondary'>Reference linked</Badge>}
                    </div>
                    <p className='mt-1 text-sm text-muted-foreground'>
                      INN: {product.inn_name || 'Not recorded'}
                      {product.dosage_strength ? ` · ${product.dosage_strength}` : ''}
                      {product.dosage_form ? ` · ${product.dosage_form}` : ''}
                    </p>
                    <p className='text-sm text-muted-foreground'>
                      SKU: {product.sku}
                      {product.manufacturer ? ` · ${product.manufacturer}` : ''}
                    </p>
                    {(product.barcode || product.gtin) && (
                      <p className='text-xs text-muted-foreground'>Barcode: {product.barcode || product.gtin}</p>
                    )}
                  </div>
                  <div className='flex items-center justify-between gap-3 sm:flex-col sm:items-end'>
                    <div className='sm:text-right'>
                      <p className='font-semibold'>{product.price.toFixed(2)}</p>
                      <p className='text-xs text-muted-foreground'>Stock {product.stock}</p>
                    </div>
                    <Button size='sm' onClick={() => addToCart(product)} disabled={product.stock < 1}>
                      <Plus className='mr-1 size-4' /> Add
                    </Button>
                  </div>
                </div>
              </div>
            ))}

            {query.trim().length >= 2 && (
              <div className='space-y-3 border-t pt-4'>
                <div className='flex flex-wrap items-center justify-between gap-2'>
                  <p className='font-medium'>International drug reference</p>
                  <Badge variant='outline'>NLM RxNorm</Badge>
                </div>
                <p className='text-xs text-muted-foreground'>
                  Clinical reference records support medicine identification. They do not confirm local registration, Rx/OTC status, package barcode, price, or availability.
                </p>
                {referenceLoading && <p className='text-sm text-muted-foreground'>Searching the reference catalog…</p>}
                {referenceError && (
                  <p className='text-sm text-destructive'>
                    The reference catalog could not be reached. Check the API connection and whether the import has been run.
                  </p>
                )}
                {!referenceLoading && !referenceError && referenceResults.map((item) => (
                  <div key={item.medicinal_product_id} className='rounded-lg border p-3'>
                    <div className='flex flex-wrap items-center gap-2'>
                      <p className='font-medium'>
                        {item.brand_name || [item.inn_name, item.strength].filter(Boolean).join(' ')}
                      </p>
                      <Badge variant='secondary'>{item.product_type === 'brand' ? 'Brand' : 'Generic'}</Badge>
                      <Badge variant='outline'>Reference only</Badge>
                    </div>
                    <p className='mt-1 text-sm text-muted-foreground'>
                      INN: {item.inn_name}
                      {item.strength ? ` · ${item.strength}` : ''}
                      {item.dosage_form ? ` · ${item.dosage_form}` : ''}
                    </p>
                    {item.manufacturer && <p className='text-sm text-muted-foreground'>{item.manufacturer}</p>}
                    {item.atc_code && <p className='text-xs text-muted-foreground'>ATC: {item.atc_code}</p>}
                    {item.gtin && <p className='text-xs text-muted-foreground'>GTIN: {item.gtin}</p>}
                    {item.regulatory_id && <p className='text-xs text-muted-foreground'>{item.regulatory_id}</p>}
                  </div>
                ))}
                {!referenceLoading && !referenceError && referenceResults.length === 0 && (
                  <p className='text-sm text-muted-foreground'>
                    No reference matches. The international catalog may not be imported yet.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className='h-fit'>
          <CardHeader>
            <div className='flex items-center justify-between gap-3'>
              <CardTitle className='flex items-center gap-2'>
                <ShoppingCart className='size-5' /> Current receipt
              </CardTitle>
              <span className='text-sm text-muted-foreground'>
                {cart.reduce((sum, item) => sum + item.quantity, 0)} items
              </span>
            </div>
          </CardHeader>
          <CardContent className='space-y-4'>
            {cart.length === 0 ? (
              <div className='rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground'>
                Search and add a product from local pharmacy stock to start a receipt.
              </div>
            ) : (
              <div className='space-y-3'>
                {cart.map((item) => (
                  <div key={item.id} className='rounded-lg border p-3'>
                    <div className='flex justify-between gap-3'>
                      <div>
                        <p className='font-medium'>{item.name}</p>
                        <p className='text-xs text-muted-foreground'>
                          SKU {item.sku} · Stock {item.stock}
                        </p>
                      </div>
                      <Button
                        variant='ghost'
                        size='icon'
                        aria-label={`Remove ${item.name}`}
                        onClick={() => setCart((items) => items.filter((entry) => entry.id !== item.id))}
                      >
                        <Trash2 className='size-4' />
                      </Button>
                    </div>
                    <div className='mt-3 flex items-center justify-between'>
                      <div className='flex items-center gap-1'>
                        <Button variant='outline' size='icon' className='size-8' aria-label='Decrease quantity' onClick={() => updateQuantity(item.id, -1)}>
                          <Minus className='size-3' />
                        </Button>
                        <span className='w-8 text-center text-sm'>{item.quantity}</span>
                        <Button variant='outline' size='icon' className='size-8' aria-label='Increase quantity' disabled={item.quantity >= item.stock} onClick={() => updateQuantity(item.id, 1)}>
                          <Plus className='size-3' />
                        </Button>
                      </div>
                      <span className='font-medium'>{(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className='rounded-lg bg-muted/50 p-4'>
              <div className='flex items-center gap-2 text-sm text-muted-foreground'>
                <UserRound className='size-4' /> Patient
              </div>
              <Button variant='outline' className='mt-2 w-full justify-start' disabled>
                Search patient
              </Button>
            </div>

            <div className='flex items-center justify-between border-t pt-4 text-lg font-semibold'>
              <span>Subtotal</span><span>{total.toFixed(2)}</span>
            </div>
            <Button className='w-full' size='lg' disabled>
              Checkout integration pending
            </Button>
            <p className='text-xs text-muted-foreground'>
              This screen currently supports product lookup and a local draft receipt. Payment and stock deduction are not connected here.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
