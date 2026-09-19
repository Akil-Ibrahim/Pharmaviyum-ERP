import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { apiFetch } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type Order = { id: number; patient_id: number; total_amount: number; status: string; created_at: string }

export const Route = createFileRoute('/_authenticated/orders')({ component: OrdersPage })

function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiFetch<Order[]>('/api/v1/orders/?limit=50')
      .then(setOrders)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unable to load orders'))
      .finally(() => setLoading(false))
  }, [])

  const completed = orders.filter((order) => order.status === 'completed')
  const pending = orders.filter((order) => order.status === 'pending')
  const cancelled = orders.filter((order) => order.status === 'cancelled')
  const revenue = completed.reduce((sum, order) => sum + order.total_amount, 0)

  return (
    <div className='space-y-6 p-6'>
      <div><h1 className='text-2xl font-bold tracking-tight'>Orders</h1><p className='text-muted-foreground'>Sales orders, fulfillment status, and patient purchase history.</p></div>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <Stat title='Orders' value={orders.length} />
        <Stat title='Completed' value={completed.length} />
        <Stat title='Pending' value={pending.length} />
        <Stat title='Completed revenue' value={new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(revenue)} />
      </div>
      <Card>
        <CardHeader><CardTitle>Order ledger</CardTitle></CardHeader>
        <CardContent>
          {loading && <p className='text-sm text-muted-foreground'>Loading orders...</p>}
          {error && <p className='text-sm text-destructive'>{error}</p>}
          {!loading && !error && orders.length === 0 && <p className='text-sm text-muted-foreground'>No orders found.</p>}
          {!loading && !error && orders.length > 0 && (
            <div className='overflow-x-auto'>
              <table className='w-full text-sm'>
                <thead><tr className='border-b text-left text-muted-foreground'><th className='p-3'>Order</th><th className='p-3'>Patient</th><th className='p-3'>Status</th><th className='p-3 text-right'>Amount</th><th className='p-3'>Created</th></tr></thead>
                <tbody>{orders.map((order) => <tr key={order.id} className='border-b last:border-0'>
                  <td className='p-3 font-medium'>#{order.id}</td><td className='p-3'>{order.patient_id}</td><td className='p-3'><span className='rounded-full bg-muted px-2.5 py-1 text-xs'>{order.status}</span></td><td className='p-3 text-right'>{order.total_amount.toFixed(2)}</td><td className='p-3 text-muted-foreground'>{new Date(order.created_at).toLocaleString()}</td>
                </tr>)}</tbody>
              </table>
              <p className='mt-3 text-xs text-muted-foreground'>Cancelled orders: {cancelled.length}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
function Stat({title,value}:{title:string;value:string|number}) { return <div className='rounded-2xl border bg-card p-4 shadow-sm'><p className='text-sm text-muted-foreground'>{title}</p><p className='mt-2 text-2xl font-bold'>{value}</p></div> }
