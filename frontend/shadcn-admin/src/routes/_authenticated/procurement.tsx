import { ClipboardList, PackageCheck, Search, Truck } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export const Route = createFileRoute('/_authenticated/procurement')({ component: ProcurementPage })

const stages = ['Draft', 'Ordered', 'Shipped', 'Receiving', 'Completed']

function ProcurementPage() {
  return <div className='space-y-6 p-6'>
    <div><h1 className='text-2xl font-bold tracking-tight'>Procurement</h1><p className='text-muted-foreground'>Supplier purchasing, purchase orders, receiving, and stock intake.</p></div>
    <div className='grid gap-4 md:grid-cols-3'><Metric icon={ClipboardList} title='Purchase Orders' /><Metric icon={Truck} title='In Receiving' /><Metric icon={PackageCheck} title='Received Today' /></div>
    <Card><CardHeader><CardTitle>Purchase Orders</CardTitle><div className='relative max-w-sm'><Search className='absolute left-3 top-3 size-4 text-muted-foreground' /><Input className='pl-9' placeholder='Search purchase orders, suppliers...' /></div></CardHeader><CardContent><div className='grid gap-2 md:grid-cols-5'>{stages.map((stage, index) => <div key={stage} className='rounded-xl border bg-muted/20 p-4'><div className='flex items-center justify-between gap-2'><span className='text-sm font-medium'>{stage}</span><Badge variant='outline'>—</Badge></div>{index < stages.length - 1 && <p className='mt-2 text-xs text-muted-foreground'>Next: {stages[index + 1]}</p>}</div>)}</div><div className='mt-5 rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground'>Purchase order data will appear here when the procurement API is connected.</div></CardContent></Card>
  </div>
}

function Metric({ icon: Icon, title }: { icon: typeof Truck; title: string }) {
  return <Card><CardContent className='p-4'><Icon className='size-4 text-primary' /><p className='mt-3 text-xs text-muted-foreground'>{title}</p><p className='mt-1 text-2xl font-semibold'>—</p><p className='mt-1 text-xs text-muted-foreground'>Backend metric pending</p></CardContent></Card>
}
