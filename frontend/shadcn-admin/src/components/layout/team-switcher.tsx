import { SidebarMenu, SidebarMenuItem } from '@/components/ui/sidebar'

type TeamSwitcherProps = {
  teams: {
    name: string
    logo: string
    plan: string
  }[]
}

export function TeamSwitcher({ teams }: TeamSwitcherProps) {
  const brand = teams[0] ?? {
    name: 'Pharmaviyum',
    logo: '/images/pharmaviyum_logo.png',
    plan: 'Pharmacy workflow',
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <div className='flex min-h-12 items-center gap-2 rounded-lg px-2 py-1 group-data-[collapsible=icon]:justify-center'>
          <div className='size-10 shrink-0 overflow-hidden rounded-lg bg-background group-data-[collapsible=icon]:size-9'>
            <img
              src={brand.logo}
              alt=''
              className='size-full rounded-lg object-cover'
            />
          </div>
          <div className='grid min-w-0 flex-1 text-start leading-tight group-data-[collapsible=icon]:hidden'>
            <span className='pharmaviyum-brand block truncate text-xs font-bold text-black dark:text-white'>
              {brand.name}
            </span>
          </div>
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
