import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Barcode,
  ClipboardList,
  CreditCard,
  Search,
  ShoppingCart,
  UserRound,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export const Route = createFileRoute('/_authenticated/pos')({
  component: POSPage,
})

function POSPage() {
  const [query, setQuery] = useState('')
  const [patient, setPatient] = useState('')
  const [hasItem, setHasItem] = useState(false)

  return (
    <div className='space-y-6 p-6'>
      <div className='flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between'>
        <div className='flex items-center gap-3'>
          <div className='flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground'>
            <ClipboardList className='size-5' />
          </div>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>POS</h1>
            <p className='text-sm text-muted-foreground'>
              Pharmacy dispensing and point-of-sale workspace.
            </p>
          </div>
        </div>
        <Badge variant='outline'>FEFO-aware workflow</Badge>
      </div>

      <div className='grid gap-6 xl:grid-cols-[1.45fr_0.9fr]'>
        <Card>
          <CardHeader>
            <CardTitle>Product Search</CardTitle>
            <p className='text-sm text-muted-foreground'>
              Search by product name, INN / active substance, or barcode.
            </p>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='relative'>
              <Search className='absolute top-3 left-3 size-4 text-muted-foreground' />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className='pr-11 pl-9'
                placeholder='Search medicine, INN, barcode...'
              />
              <Barcode className='absolute top-3 right-3 size-4 text-muted-foreground' />
            </div>
            <div className='rounded-xl border bg-muted/20 p-5'>
              {!query ? (
                <div className='py-10 text-center'>
                  <ShoppingCart className='mx-auto size-8 text-muted-foreground' />
                  <p className='mt-3 font-medium'>
                    Search for a product to begin
                  </p>
                  <p className='mt-1 text-sm text-muted-foreground'>
                    Reference and generic products remain distinct throughout
                    selection.
                  </p>
                </div>
              ) : (
                <button
                  type='button'
                  className='w-full rounded-lg border bg-card p-4 text-left hover:bg-muted/40'
                  onClick={() => setHasItem(true)}
                >
                  <div className='flex items-center justify-between gap-3'>
                    <div>
                      <p className='font-medium'>Product search result</p>
                      <p className='text-sm text-muted-foreground'>
                        Open product and batch / FEFO selection
                      </p>
                    </div>
                    <Badge variant='secondary'>Select</Badge>
                  </div>
                </button>
              )}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Patient</CardTitle>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='relative'>
              <UserRound className='absolute top-3 left-3 size-4 text-muted-foreground' />
              <Input
                value={patient}
                onChange={(e) => setPatient(e.target.value)}
                className='pl-9'
                placeholder='Search patient...'
              />
            </div>
            <div className='rounded-lg border border-dashed p-4 text-sm text-muted-foreground'>
              Patient selection is optional until dispensing requires a patient
              or prescription.
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Current Sale</CardTitle>
          <p className='text-sm text-muted-foreground'>
            Product → Batch / FEFO → Order → Payment → Dispensing → Receipt
          </p>
        </CardHeader>
        <CardContent>
          {!hasItem ? (
            <div className='rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground'>
              No items in the cart.
            </div>
          ) : (
            <div className='space-y-4'>
              <div className='rounded-xl border p-4'>
                <div className='flex flex-wrap items-center justify-between gap-3'>
                  <div>
                    <p className='font-medium'>Selected product</p>
                    <p className='text-sm text-muted-foreground'>
                      Batch selection and price are supplied by the backend
                      workflow.
                    </p>
                  </div>
                  <div className='flex gap-2'>
                    <Badge variant='outline'>FEFO pending</Badge>
                    <Badge variant='outline'>Qty 1</Badge>
                  </div>
                </div>
              </div>
              <div className='flex justify-end'>
                <Button disabled>
                  <CreditCard className='mr-2 size-4' />
                  Proceed to payment
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
