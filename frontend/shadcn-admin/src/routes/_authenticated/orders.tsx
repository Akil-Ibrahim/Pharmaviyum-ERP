import { useEffect, useMemo, useState } from 'react'
import { Search, RefreshCw } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { apiFetch } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

type Order = { id: number; patient_id: number; total_amount: number; status: string; created_at: string }

export const Route = createFileRoute('/_authenticated/orders')({ component: OrdersPage })

function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  const load = () => {
    setLoading(true); setError(null)
    apiFetch<Order[]>('/api/v1/orders/?limit=50').then(setOrders).catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load orders')).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const completed = orders.filter((order) => order.status === 'completed')
  const pending = orders.filter((order) => order.status === 'pending')
  const cancelled = orders.filter((order) => order.status === 'cancelled')
  const revenue = completed.reduce((sum, order) => sum + order.total_amount, 0)
  const filtered = useMemo(() => {
    const q=query.trim().toLowerCase()
    return q ? orders.filter((o)=>String(o.id).includes(q)||String(o.patient_id).includes(q)||o.status.toLowerCase().includes(q)) : orders
  }, [orders,query])

  return <div className='space-y-6 p-6'>
    <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'><div><h1 className='text-2xl font-bold tracking-tight'>Orders</h1><p className='text-muted-foreground'>Sales orders, fulfillment status, and patient purchase history.</p></div><Button variant='outline' size='sm' onClick={load} disabled={loading}><RefreshCw className='mr-2 size-4'/>Refresh</Button></div>
    <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'><Stat title='Orders' value={orders.length}/><Stat title='Completed' value={completed.length}/><Stat title='Pending' value={pending.length}/><Stat title='Completed revenue' value={new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(revenue)}/></div>
    <Card><CardHeader><div className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'><CardTitle>Order ledger</CardTitle><div className='relative w-full sm:max-w-sm'><Search className='absolute left-2.5 top-2.5 size-4 text-muted-foreground'/><Input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder='Search orders...' className='pl-9'/></div></div></CardHeader><CardContent>
      {loading&&<p className='text-sm text-muted-foreground'>Loading orders...</p>}{error&&<p className='text-sm text-destructive'>{error}</p>}{!loading&&!error&&filtered.length===0&&<p className='text-sm text-muted-foreground'>No orders match the current search.</p>}
      {!loading&&!error&&filtered.length>0&&<div className='overflow-x-auto rounded-md border'><table className='w-full text-sm'><thead><tr className='border-b bg-muted/40 text-left text-muted-foreground'><th className='p-3'>Order</th><th className='p-3'>Patient</th><th className='p-3'>Status</th><th className='p-3 text-right'>Amount</th><th className='p-3'>Created</th></tr></thead><tbody>{filtered.map((order)=><tr key={order.id} className='border-b last:border-0 hover:bg-muted/30'><td className='p-3 font-medium'>#{order.id}</td><td className='p-3'>{order.patient_id}</td><td className='p-3'><Badge variant='outline' className={order.status==='completed'?'bg-green-500/15 text-green-700 dark:text-green-300':order.status==='cancelled'?'bg-red-500/15 text-red-700 dark:text-red-300':'bg-amber-500/15 text-amber-700 dark:text-amber-300'}>{order.status}</Badge></td><td className='p-3 text-right'>{order.total_amount.toFixed(2)}</td><td className='p-3 text-muted-foreground'>{new Date(order.created_at).toLocaleString()}</td></tr>)}</tbody></table><p className='mt-3 text-xs text-muted-foreground'>Cancelled orders: {cancelled.length}</p></div>}
    </CardContent></Card>
  </div>
}
function Stat({title,value}:{title:string;value:string|number}) { return <Card><CardContent className='p-4'><p className='text-xs font-medium text-muted-foreground'>{title}</p><p className='mt-2 text-2xl font-semibold'>{value}</p></CardContent></Card> }
