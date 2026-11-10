import { Outlet } from '@tanstack/react-router'
import { Monitor, Bell, Palette, Wrench, UserCog } from 'lucide-react'
import { Separator } from '@/components/ui/separator'
import { Main } from '@/components/layout/main'
import { PageHeader } from '@/components/page-header'
import { SidebarNav } from './components/sidebar-nav'

const sidebarNavItems = [
  {
    title: 'Profile',
    href: '/settings',
    icon: <UserCog size={18} />,
  },
  {
    title: 'Account',
    href: '/settings/account',
    icon: <Wrench size={18} />,
  },
  {
    title: 'Appearance',
    href: '/settings/appearance',
    icon: <Palette size={18} />,
  },
  {
    title: 'Notifications',
    href: '/settings/notifications',
    icon: <Bell size={18} />,
  },
  {
    title: 'Display',
    href: '/settings/display',
    icon: <Monitor size={18} />,
  },
]

export function Settings() {
  return (
    <Main fixed>
      <PageHeader
        title='Settings'
        description='Manage your account settings and set e-mail preferences.'
      />
      <Separator className='my-4 lg:my-6' />
      <div className='flex min-h-0 min-w-0 flex-1 flex-col gap-4 overflow-y-auto lg:flex-row lg:gap-12 lg:overflow-hidden'>
        <aside className='w-full shrink-0 lg:sticky lg:top-0 lg:w-1/5'>
          <SidebarNav items={sidebarNavItems} />
        </aside>
        <div className='min-h-0 w-full min-w-0 flex-1 p-1 lg:overflow-y-auto'>
          <Outlet />
        </div>
      </div>
    </Main>
  )
}
