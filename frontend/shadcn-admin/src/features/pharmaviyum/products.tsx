import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Package, RefreshCw, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type Product = { id: number; name: string; sku: string; description: string | null; price: number; stock: number; is_active: boolean; prescription_required: boolean }

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  const load = () => {
    setLoading(true); setError(null)
    apiFetch<Product[]>('/api/v1/products/?limit=50')
      .then(setProducts)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load products'))
      .finally(() => setLoading(false))
  }

  async function togglePrescriptionRequirement(product: Product) {
    const prescriptionRequired = !product.prescription_required
    if (!prescriptionRequired && !window.confirm(
      `Confirm that "${product.name}" is legally classified as OTC in your pharmacy market?`,
    )) return
    try {
      const updated = await apiFetch<Product>(`/api/v1/products/${product.id}`, {
        method: 'PUT',
        body: JSON.stringify({ prescription_required: prescriptionRequired }),
      })
      setProducts((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update dispensing classification')
    }
  }
  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer) }, [])

  const filtered = useMemo(() => {
    const q=query.trim().toLowerCase()
    return q ? products.filter((p) => [p.name,p.sku,p.description ?? ''].some((v)=>v.toLowerCase().includes(q))) : products
  }, [products,query])
  const active=products.filter((p)=>p.is_active).length
  const lowStock=products.filter((p)=>p.stock <= 10).length
  const catalogValue=products.reduce((sum,p)=>sum+p.price*p.stock,0)

  return <div className='space-y-6 p-6'>
    <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'><div><h1 className='text-2xl font-bold tracking-tight'>Products</h1><p className='text-muted-foreground'>Medicines and pharmacy products with catalog, stock, and pricing data.</p></div><Button variant='outline' size='sm' onClick={load} disabled={loading}><RefreshCw className='mr-2 size-4'/>Refresh</Button></div>
    <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
      <Metric label='Products' value={products.length} icon={<Package className='size-4'/>}/>
      <Metric label='Active' value={active} tone='green'/>
      <Metric label='Low stock' value={lowStock} tone='amber'/>
      <Metric label='Catalog stock value' value={new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(catalogValue)} tone='blue'/>
    </div>
    <Card><CardHeader><div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'><CardTitle>Product catalog</CardTitle><div className='relative w-full sm:max-w-sm'><Search className='absolute left-2.5 top-2.5 size-4 text-muted-foreground'/><Input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder='Search products...' className='pl-9'/></div></div></CardHeader><CardContent>
      {loading && <p className='text-sm text-muted-foreground'>Loading products...</p>}
      {error && <p className='text-sm text-destructive'>{error}</p>}
      {!loading&&!error&&filtered.length===0&&<p className='text-sm text-muted-foreground'>No products match the current search.</p>}
      {!loading&&!error&&filtered.length>0&&<div className='overflow-x-auto rounded-md border'><table className='w-full text-sm'><thead><tr className='border-b bg-muted/40 text-left text-muted-foreground'><th className='p-3'>Product</th><th className='p-3'>SKU</th><th className='p-3 text-right'>Price</th><th className='p-3 text-right'>Stock</th><th className='p-3'>Dispensing rule</th><th className='p-3'>Status</th></tr></thead><tbody>{filtered.map((p)=><tr key={p.id} className='border-b last:border-0 hover:bg-muted/30'><td className='p-3 font-medium'>{p.name}</td><td className='p-3 text-muted-foreground'>{p.sku}</td><td className='p-3 text-right'>{p.price.toFixed(2)}</td><td className='p-3 text-right'>{p.stock}</td><td className='p-3'><div className='flex flex-wrap items-center gap-2'><Badge variant={p.prescription_required?'destructive':'secondary'}>{p.prescription_required?'Prescription required':'OTC'}</Badge><Button variant='outline' size='sm' onClick={() => void togglePrescriptionRequirement(p)}>{p.prescription_required?'Mark OTC':'Mark Rx-only'}</Button></div></td><td className='p-3'><Badge variant='outline' className={p.is_active?'bg-green-500/15 text-green-700 dark:text-green-300':'bg-muted text-muted-foreground'}>{p.is_active?'Active':'Inactive'}</Badge></td></tr>)}</tbody></table></div>}
    </CardContent></Card>
  </div>
}
function Metric({label,value,tone='default',icon}:{label:string;value:string|number;tone?:string;icon?:ReactNode}){return <Card><CardContent className='p-4'><div className='flex items-center gap-2 text-xs font-medium text-muted-foreground'>{icon}{label}</div><p className={'mt-2 text-2xl font-semibold '+(tone==='green'?'text-emerald-600 dark:text-emerald-400':tone==='amber'?'text-amber-600 dark:text-amber-400':tone==='blue'?'text-sky-600 dark:text-sky-400':'')}>{value}</p></CardContent></Card>}
