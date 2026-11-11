import { Activity, RefreshCw, ServerCog } from 'lucide-react'
import { Link, createFileRoute } from '@tanstack/react-router'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const Route = createFileRoute('/_authenticated/settings/developer')({
  component: DeveloperSettingsPage,
})

function DeveloperSettingsPage() {
  return (
    <main className='p-4 md:p-6'>
      <div className='space-y-6'>
        <div>
          <h1 className='text-2xl font-semibold tracking-tight'>Developer Settings</h1>
          <p className='mt-1 text-sm text-muted-foreground'>
            System diagnostics, ERP integrations, and synchronization tools.
          </p>
        </div>

        <section className='grid gap-4 md:grid-cols-2'>
          <Link to='/system-status' className='rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring'>
            <Card className='h-full transition-colors hover:bg-accent/40'>
              <CardHeader>
                <div className='mb-2 flex size-10 items-center justify-center rounded-lg bg-muted'>
                  <Activity className='size-5' />
                </div>
                <CardTitle>System Status</CardTitle>
                <CardDescription>
                  Monitor application health and the availability of core dependencies.
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>

          <Card className='h-full'>
            <CardHeader>
              <div className='mb-2 flex size-10 items-center justify-center rounded-lg bg-muted'>
                <ServerCog className='size-5' />
              </div>
              <CardTitle>Integrations</CardTitle>
              <CardDescription>
                Manage external ERP connections and inspect synchronization activity.
              </CardDescription>
              <div className='mt-2 flex flex-col gap-2'>
                <Link to='/erp-systems' className='inline-flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'>
                  <ServerCog className='size-4 text-muted-foreground' />
                  ERP Connections
                </Link>
                <Link to='/sync-events' className='inline-flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'>
                  <RefreshCw className='size-4 text-muted-foreground' />
                  Sync History
                </Link>
              </div>
            </CardHeader>
          </Card>
        </section>
      </div>
    </main>
  )
}
