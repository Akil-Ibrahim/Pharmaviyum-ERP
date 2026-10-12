import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
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
        <SidebarMenuButton
          size='lg'
          className='cursor-default hover:bg-transparent active:bg-transparent'
          aria-label={`${brand.name} pharmacy workspace`}
        >
          <div className='flex size-10 shrink-0 items-center justify-center rounded-xl border border-primary/15 bg-background shadow-sm ring-1 ring-border/40'>
            <img
              src={brand.logo}
              alt=''
              className='size-8 object-contain'
            />
          </div>
          <div className='grid min-w-0 flex-1 text-start leading-tight'>
            <span className='pharmaviyum-brand block truncate text-base font-bold text-black dark:text-white'>
              {brand.name}
            </span>
            <span className='pharmacy-workflow block truncate text-xs font-medium text-muted-foreground'>
              {brand.plan}
            </span>
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
