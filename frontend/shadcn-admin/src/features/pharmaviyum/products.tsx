import { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type Product = {
  id: number
  name: string
  sku: string
  description: string | null
  dosage_strength: string | null
  dosage_form: string | null
  manufacturer: string | null
  inn_name: string | null
  gtin: string | null
  barcode: string | null
  regulatory_id: string | null
  medicinal_product_id: number | null
  is_active: boolean
}

const SEARCH_MIN_LENGTH = 2
const SEARCH_LIMIT = 100

function searchableFields(product: Product) {
  return [
    product.name,
    product.sku,
    product.description ?? '',
    product.dosage_strength ?? '',
    product.dosage_form ?? '',
    product.manufacturer ?? '',
    product.inn_name ?? '',
    product.gtin ?? '',
    product.barcode ?? '',
    product.regulatory_id ?? '',
  ]
}

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const normalizedQuery = query.trim()

  useEffect(() => {
    const controller = new AbortController()
    const search = normalizedQuery.length >= SEARCH_MIN_LENGTH
    const path = search
      ? `/api/v1/products/search?q=${encodeURIComponent(normalizedQuery)}&limit=${SEARCH_LIMIT}`
      : '/api/v1/products/?limit=50'

    const timer = window.setTimeout(
      () => {
        setLoading(true)
        setError(null)
        apiFetch<Product[]>(path, { signal: controller.signal })
          .then((result) => setProducts(result))
          .catch((err: unknown) => {
            if (controller.signal.aborted) return
            setError(
              err instanceof Error
                ? err.message
                : 'Unable to load the product catalog'
            )
          })
          .finally(() => {
            if (!controller.signal.aborted) setLoading(false)
          })
      },
      search ? 250 : 0
    )

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [normalizedQuery])

  const displayedProducts = useMemo(() => {
    if (normalizedQuery.length !== 1) return products
    const term = normalizedQuery.toLocaleLowerCase()
    return products.filter((product) =>
      searchableFields(product).some((value) =>
        value.toLocaleLowerCase().includes(term)
      )
    )
  }, [normalizedQuery, products])

  const refresh = () => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    const search = normalizedQuery.length >= SEARCH_MIN_LENGTH
    const path = search
      ? `/api/v1/products/search?q=${encodeURIComponent(normalizedQuery)}&limit=${SEARCH_LIMIT}`
      : '/api/v1/products/?limit=50'
    apiFetch<Product[]>(path, { signal: controller.signal })
      .then(setProducts)
      .catch((err: unknown) =>
        setError(
          err instanceof Error ? err.message : 'Unable to load the product catalog'
        )
      )
      .finally(() => setLoading(false))
  }

  return (
    <div className='pharmacy-data-page pharmacy-products-page space-y-6 p-6'>
      <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Products</h1>
          <p className='text-muted-foreground'>
            Search sellable pharmacy products by medicine name, active ingredient,
            strength, dosage form, manufacturer, barcode, or regulatory identifier.
          </p>
        </div>
        <Button variant='outline' size='sm' onClick={refresh} disabled={loading}>
          <RefreshCw className='mr-2 size-4' aria-hidden='true' />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
            <CardTitle>Product catalog</CardTitle>
            <div className='relative w-full sm:max-w-md'>
              <Search
                className='absolute left-2.5 top-2.5 size-4 text-muted-foreground'
                aria-hidden='true'
              />
              <Input
                aria-label='Search sellable pharmacy products'
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder='Search medicines, ingredients, strength, barcode...'
                className='pl-9'
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className='space-y-3'>
          {normalizedQuery.length === 1 && (
            <p className='text-sm text-muted-foreground'>
              Enter at least {SEARCH_MIN_LENGTH} characters to search the full
              sellable product catalog.
            </p>
          )}
          <div className='flex items-center justify-between gap-3 text-sm text-muted-foreground'>
            <span>
              {normalizedQuery.length >= SEARCH_MIN_LENGTH
                ? `Up to ${SEARCH_LIMIT} matching products`
                : 'Recently available products'}
            </span>
            <span aria-live='polite' aria-atomic='true'>
              {loading
                ? 'Loading products...'
                : `${displayedProducts.length} shown`}
            </span>
          </div>

          {error && (
            <p role='alert' className='text-sm text-destructive'>
              {error}
            </p>
          )}
          {!loading && !error && displayedProducts.length === 0 && (
            <p className='py-8 text-center text-sm text-muted-foreground'>
              No sellable products match this search.
            </p>
          )}
          {displayedProducts.length > 0 && (
            <div className='overflow-x-auto rounded-md border'>
              <table className='w-full text-sm'>
                <caption className='sr-only'>
                  Sellable pharmacy products and medication identifiers
                </caption>
                <thead>
                  <tr className='border-b bg-muted/40 text-left text-muted-foreground'>
                    <th scope='col' className='p-3'>Product</th>
                    <th scope='col' className='p-3'>Active ingredient</th>
                    <th scope='col' className='p-3'>Strength</th>
                    <th scope='col' className='p-3'>Dosage form</th>
                    <th scope='col' className='p-3'>Manufacturer</th>
                    <th scope='col' className='p-3'>Identifiers</th>
                    <th scope='col' className='p-3'>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedProducts.map((product) => (
                    <tr
                      key={product.id}
                      className='border-b last:border-0 hover:bg-muted/30'
                    >
                      <td className='p-3'>
                        <div className='font-medium'>{product.name}</div>
                        <div className='text-xs text-muted-foreground'>
                          SKU: {product.sku}
                        </div>
                      </td>
                      <td className='p-3'>{product.inn_name || '—'}</td>
                      <td className='p-3'>{product.dosage_strength || '—'}</td>
                      <td className='p-3'>{product.dosage_form || '—'}</td>
                      <td className='p-3'>{product.manufacturer || '—'}</td>
                      <td className='p-3'>
                        <div>{product.barcode || product.gtin || '—'}</div>
                        {product.regulatory_id && (
                          <div className='text-xs text-muted-foreground'>
                            {product.regulatory_id}
                          </div>
                        )}
                      </td>
                      <td className='p-3'>
                        <Badge
                          variant='outline'
                          className={
                            product.is_active
                              ? 'bg-green-500/15 text-green-700 dark:text-green-300'
                              : 'bg-muted text-muted-foreground'
                          }
                        >
                          {product.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
