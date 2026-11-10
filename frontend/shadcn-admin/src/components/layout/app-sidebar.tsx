import { useLayout } from '@/context/layout-provider'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarTrigger,
} from '@/components/ui/sidebar'
// import { AppTitle } from './app-title'
import { sidebarData } from './data/sidebar-data'
import { NavGroup } from './nav-group'
import { NavUser } from './nav-user'
import { TeamSwitcher } from './team-switcher'

export function AppSidebar() {
  const { collapsible, variant } = useLayout()
  return (
    <Sidebar
      collapsible={collapsible}
      variant={variant}
      className='border-sidebar-border/80'
    >
      <SidebarHeader className='px-2 py-3'>
        <div className='flex items-center gap-1 group-data-[collapsible=icon]:flex-col'>
          <div className='min-w-0 flex-1 group-data-[collapsible=icon]:w-full group-data-[collapsible=icon]:flex-none'>
            <TeamSwitcher teams={sidebarData.teams} />
          </div>
          <SidebarTrigger
            aria-label='Collapse or expand navigation'
            className='size-7 shrink-0 rounded-lg text-[#64748B] hover:bg-[#F1F5F9] hover:text-[#0F172A]'
          />
        </div>
      </SidebarHeader>
      <SidebarContent className='gap-0 px-1 py-2'>
        {sidebarData.navGroups.map((props) => (
          <NavGroup key={props.title} {...props} />
        ))}
      </SidebarContent>
      <SidebarFooter className='border-t border-sidebar-border/70 px-3 py-3'>
        <NavUser user={sidebarData.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
