import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiFetch } from '@/lib/api-client'

type Product = {
  id: number
  name: string
  sku: string
  description: string | null
  price: number
  stock: number
  is_active: boolean
}

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    apiFetch<Product[]>('/api/v1/products/?limit=50')
      .then((data) => {
        if (!cancelled) setProducts(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unable to load products')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Products</h1>
        <p className='text-muted-foreground'>
          Medicines and pharmacy products with catalog and pricing data.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product catalog</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && (
            <p className='text-sm text-muted-foreground'>Loading products...</p>
          )}
          {error && !loading && (
            <p className='text-sm text-destructive'>{error}</p>
          )}
          {!loading && !error && products.length === 0 && (
            <p className='text-sm text-muted-foreground'>
              No active products found.
            </p>
          )}
          {!loading && !error && products.length > 0 && (
            <div className='space-y-2'>
              {products.map((product) => (
                <div
                  key={product.id}
                  className='flex items-center justify-between rounded-lg border p-4'
                >
                  <div className='min-w-0'>
                    <p className='font-medium'>{product.name}</p>
                    <p className='text-sm text-muted-foreground'>
                      {product.sku}
                    </p>
                  </div>
                  <div className='text-right'>
                    <p className='font-medium'>{product.price.toFixed(2)}</p>
                    <p className='text-sm text-muted-foreground'>
                      Stock: {product.stock}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
