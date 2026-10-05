import { Activity, AlertTriangle, Bot, ClipboardList, Clock3, PackageSearch, Pill, ReceiptText, Users } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const actions = [
  { title: 'Open POS', description: 'Start a new sale or continue a receipt.', icon: ReceiptText },
  { title: 'Review prescriptions', description: 'Check prescriptions waiting for dispensing.', icon: Pill },
  { title: 'Check stock alerts', description: 'Review low-stock and critical inventory items.', icon: PackageSearch },
  { title: 'Review expiry alerts', description: 'See products approaching expiry.', icon: AlertTriangle },
]

export function PharmacistWorkspace() {
  return (
    <div className='space-y-6 p-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Pharmacist Workspace</h1>
        <p className='text-muted-foreground'>A focused workspace for the pharmacist's daily operations.</p>
      </div>

      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <Metric label='Today' value='18' detail='transactions' icon={Activity} />
        <Metric label='Pending' value='6' detail='prescriptions' icon={ClipboardList} />
        <Metric label='Alerts' value='4' detail='inventory items' icon={AlertTriangle} />
        <Metric label='Patients' value='12' detail='today' icon={Users} />
      </div>

      <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]'>
        <Card>
          <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
          <CardContent className='grid gap-3 sm:grid-cols-2'>
            {actions.map(({ title, description, icon: Icon }) => (
              <Button key={title} variant='outline' className='h-auto justify-start p-4 text-left'>
                <Icon className='mr-3 size-5 shrink-0' />
                <span><span className='block font-medium'>{title}</span><span className='block text-xs font-normal text-muted-foreground'>{description}</span></span>
              </Button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>AI Assistant</CardTitle></CardHeader>
          <CardContent>
            <div className='rounded-lg border bg-muted/30 p-4'>
              <Bot className='mb-3 size-5' />
              <p className='text-sm font-medium'>Mortarium AI</p>
              <p className='mt-1 text-sm text-muted-foreground'>Ask about permitted pharmacy data, routine tasks, patients, inventory, or prescriptions.</p>
              <Button className='mt-4 w-full'>Open AI Assistant</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Today's Activity</CardTitle></CardHeader>
        <CardContent className='grid gap-3 sm:grid-cols-3'>
          <ActivityItem icon={Clock3} label='Shift' value='09:00–18:00' />
          <ActivityItem icon={ReceiptText} label='Recent transaction' value='Receipt #1042' />
          <ActivityItem icon={PackageSearch} label='Next task' value='Review stock alerts' />
        </CardContent>
      </Card>
    </div>
  )
}

function Metric({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: typeof Activity }) {
  return <Card><CardContent className='p-4'><div className='flex items-center gap-2 text-xs font-medium text-muted-foreground'><Icon className='size-4' />{label}</div><p className='mt-2 text-2xl font-semibold'>{value}</p><p className='text-xs text-muted-foreground'>{detail}</p></CardContent></Card>
}

function ActivityItem({ icon: Icon, label, value }: { icon: typeof Clock3; label: string; value: string }) {
  return <div className='rounded-lg border p-4'><div className='flex items-center gap-2 text-xs text-muted-foreground'><Icon className='size-4' />{label}</div><p className='mt-2 font-medium'>{value}</p></div>
}
