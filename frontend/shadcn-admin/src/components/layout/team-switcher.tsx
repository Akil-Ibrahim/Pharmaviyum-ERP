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
          <div className='flex h-10 w-14 shrink-0 items-center justify-center rounded-md border border-primary/15 bg-background shadow-sm ring-1 ring-border/40 group-data-[collapsible=icon]:size-9'>
            <img
              src={brand.logo}
              alt=''
              className='h-8 w-12 object-contain group-data-[collapsible=icon]:size-7'
            />
          </div>
          <div className='grid min-w-0 flex-1 text-start leading-tight group-data-[collapsible=icon]:hidden'>
            <span className='pharmaviyum-brand block truncate text-base font-bold text-black dark:text-white'>
              {brand.name}
            </span>
            <span className='pharmacy-workflow block truncate text-xs font-medium text-muted-foreground'>
              {brand.plan}
            </span>
          </div>
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
