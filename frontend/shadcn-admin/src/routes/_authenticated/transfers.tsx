import { createFileRoute } from '@tanstack/react-router'
import { ArrowLeftRight, CheckCircle2, Package, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export const Route = createFileRoute('/_authenticated/transfers')({
  component: TransfersPage,
})

const stages = ['Requested', 'Approved', 'In transit', 'Received']

function TransfersPage() {
  return (
    <div className='space-y-6 p-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Transfers</h1>
        <p className='text-muted-foreground'>
          Move stock between pharmacy locations with batch traceability.
        </p>
      </div>
      <div className='grid gap-4 xl:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <ArrowLeftRight className='size-4 text-primary' />
              Transfer Workflow
            </CardTitle>
          </CardHeader>
          <CardContent className='grid gap-2 sm:grid-cols-4'>
            {stages.map((stage) => (
              <div
                key={stage}
                className='rounded-xl border bg-muted/20 p-4 text-center'
              >
                <p className='text-lg font-semibold'>—</p>
                <p className='text-xs text-muted-foreground'>{stage}</p>
                <Badge variant='outline' className='mt-2'>
                  Status
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Search Transfers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='relative'>
              <Search className='absolute top-3 left-3 size-4 text-muted-foreground' />
              <Input
                className='pl-9'
                placeholder='Transfer ID, pharmacy, product...'
              />
            </div>
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Transfer Ledger</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='rounded-xl border border-dashed p-8 text-center'>
            <Package className='mx-auto size-8 text-muted-foreground' />
            <p className='mt-3 font-medium'>No transfer records loaded</p>
            <p className='mt-1 text-sm text-muted-foreground'>
              The workflow is ready for source pharmacy, destination pharmacy,
              products, quantities, batches, FEFO, shipment, and receiving.
            </p>
            <div className='mt-4 flex justify-center'>
              <Badge variant='outline'>
                <CheckCircle2 className='mr-1 size-3' />
                Traceability ready
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
