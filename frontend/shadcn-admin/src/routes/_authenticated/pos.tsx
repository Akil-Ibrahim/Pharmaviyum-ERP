import { createFileRoute } from '@tanstack/react-router'
import { ClipboardList } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/pos')({
  component: POSPage,
})

function POSPage() {
  return (
    <div className='space-y-6 p-6'>
      <div className='flex items-center gap-3'>
        <div className='flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground'>
          <ClipboardList className='size-5' />
        </div>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>POS</h1>
          <p className='text-sm text-muted-foreground'>
            Pharmacy point-of-sale workspace
          </p>
        </div>
      </div>

      <div className='rounded-lg border bg-card p-6'>
        <h2 className='font-semibold'>Pharmacy Sales</h2>
        <p className='mt-2 text-sm text-muted-foreground'>
          This workspace will connect the pharmacy sales workflow to products,
          batches, FEFO dispensing, orders, inventory transactions, receipts,
          and patient purchases.
        </p>
      </div>
    </div>
  )
}
