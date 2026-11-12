import { Link, createFileRoute } from '@tanstack/react-router'
import {
  Activity,
  BookOpen,
  ChevronDown,
  Network,
  RefreshCw,
  ServerCog,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export const Route = createFileRoute('/_authenticated/settings/developer')({
  component: DeveloperSettingsPage,
})

function DeveloperSettingsPage() {
  return (
    <main className='space-y-6 p-4 md:p-6'>
      <header className='space-y-1'>
        <h1 className='text-2xl font-semibold tracking-tight'>
          Developer Settings
        </h1>
        <p className='text-sm text-muted-foreground'>
          Technical workspaces, infrastructure documentation, and diagnostics.
        </p>
      </header>

      <section className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
        <Card className='h-full'>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Network className='size-4' />
              Ansible
            </CardTitle>
            <CardDescription>
              Pharmacy Edge infrastructure automation, deployment standards, and
              pharmacy onboarding.
            </CardDescription>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant='outline' className='mt-2 w-fit'>
                  Ansible
                  <ChevronDown className='ml-2 size-4' />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='start'>
                <DropdownMenuItem asChild>
                  <Link to='/settings/developer/ansible'>
                    <BookOpen className='mr-2 size-4' />
                    Documentation
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardHeader>
        </Card>

        <Link to='/system-status'>
          <Card className='h-full transition-colors hover:bg-accent/40'>
            <CardHeader>
              <CardTitle className='flex items-center gap-2'>
                <Activity className='size-4' />
                System Status
              </CardTitle>
              <CardDescription>
                View application health and core dependency status.
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <ServerCog className='size-4' />
              Integrations
            </CardTitle>
            <CardDescription>
              ERP Connections and Sync History are navigation shells. Live
              backend integration is not yet connected.
            </CardDescription>
            <div className='flex flex-col gap-2'>
              <Link
                to='/erp-systems'
                className='flex items-center gap-2 text-sm hover:underline'
              >
                <ServerCog className='size-4' />
                ERP Connections
              </Link>
              <Link
                to='/sync-events'
                className='flex items-center gap-2 text-sm hover:underline'
              >
                <RefreshCw className='size-4' />
                Sync History
              </Link>
            </div>
          </CardHeader>
        </Card>
      </section>
    </main>
  )
}
