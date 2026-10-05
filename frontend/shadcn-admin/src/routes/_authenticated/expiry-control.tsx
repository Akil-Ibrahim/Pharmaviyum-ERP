import { createFileRoute } from '@tanstack/react-router'
import { AlertTriangle, CalendarClock, CheckCircle2, Search, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export const Route = createFileRoute('/_authenticated/expiry-control')({ component: ExpiryControlPage })
const views=[['Expired','Expired stock'],['Critical','≤ 7 days'],['Warning','8–30 days'],['Good','> 30 days'],['3 months','Pre-expiry view'],['9 months','Pre-expiry view'],['12 months','Pre-expiry view']]
function ExpiryControlPage(){
 return <div className='space-y-6 p-6'>
  <div><h1 className='text-2xl font-bold tracking-tight'>Expiry Control</h1><p className='text-muted-foreground'>Expiry monitoring, FEFO priorities, batch traceability, and quarantine workflow.</p></div>
  <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-4'><StatusCard icon={XCircle} title='Expired'/><StatusCard icon={AlertTriangle} title='Critical ≤7 days'/><StatusCard icon={CalendarClock} title='Warning 8–30 days'/><StatusCard icon={CheckCircle2} title='Good >30 days'/></div>
  <Card><CardHeader><CardTitle>Expiry Views</CardTitle><div className='relative max-w-sm'><Search className='absolute top-3 left-3 size-4 text-muted-foreground'/><Input className='pl-9' placeholder='Search product, batch, pharmacy...'/></div></CardHeader><CardContent className='space-y-5'><div className='grid gap-2 sm:grid-cols-2 lg:grid-cols-4'>{views.map(([label,description])=><button type='button' key={label} className='rounded-xl border p-4 text-left transition-colors hover:bg-muted/40'><p className='font-medium'>{label}</p><p className='mt-1 text-xs text-muted-foreground'>{description}</p><Badge variant='outline' className='mt-3'>— batches</Badge></button>)}</div><div className='rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground'>Batch and expiry data will be connected here. FEFO should prioritize the earliest valid batch and expired stock must remain blocked from dispensing.</div></CardContent></Card>
 </div>
}
function StatusCard({icon:Icon,title}:{icon:typeof AlertTriangle;title:string}){return <Card><CardContent className='p-4'><Icon className='size-4 text-primary'/><p className='mt-3 text-xs text-muted-foreground'>{title}</p><p className='mt-1 text-2xl font-semibold'>—</p></CardContent></Card>}
