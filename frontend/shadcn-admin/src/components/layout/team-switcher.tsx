import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarTrigger,
} from '@/components/ui/sidebar'

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
        <div className='flex min-h-12 items-center gap-2 rounded-lg px-2 py-1'>
          <div className='size-10 shrink-0 overflow-hidden rounded-lg bg-background group-data-[collapsible=icon]:size-9'>
            <img
              src={brand.logo}
              alt=''
              className='size-full rounded-lg object-cover'
            />
          </div>
          <div className='grid min-w-0 flex-1 text-start leading-tight group-data-[collapsible=icon]:hidden'>
            <span className='pharmaviyum-brand block truncate text-[15px] font-bold text-black dark:text-white'>
              {brand.name}
            </span>
          </div>
          <SidebarTrigger className='ms-auto size-8 shrink-0 group-data-[collapsible=icon]:mx-auto' />
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
