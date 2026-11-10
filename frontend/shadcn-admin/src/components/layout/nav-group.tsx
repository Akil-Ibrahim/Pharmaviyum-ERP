import { useState, type ElementType, type ReactNode } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import { NAVIGATION_ICON_COLORS, useTheme } from '@/context/theme-provider'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { Badge } from '../ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import {
  type NavCollapsible,
  type NavItem,
  type NavLink,
  type NavGroup as NavGroupProps,
} from './types'

export function NavGroup({ title, items }: NavGroupProps) {
  const { state, isMobile } = useSidebar()
  const href = useLocation({ select: (location) => location.href })
  return (
    <SidebarGroup>
      <SidebarGroupLabel className='h-7 px-3 text-[10px] font-bold tracking-[0.16em] text-muted-foreground/75 uppercase'>
        {title}
      </SidebarGroupLabel>
      <SidebarMenu className='gap-1'>
        {items.map((item) => {
          const key = `${item.title}-${item.url}`

          if (!item.items)
            return <SidebarMenuLink key={key} item={item} href={href} />

          if (state === 'collapsed' && !isMobile)
            return (
              <SidebarMenuCollapsedDropdown key={key} item={item} href={href} />
            )

          return <SidebarMenuCollapsible key={key} item={item} href={href} />
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}

function NavBadge({ children }: { children: ReactNode }) {
  return (
    <Badge className='ms-auto rounded-md border border-primary/15 bg-primary/10 px-1.5 py-0 text-[10px] font-bold text-primary shadow-none group-data-[collapsible=icon]:hidden'>
      {children}
    </Badge>
  )
}

function NavIcon({
  icon: Icon,
  active = false,
  size = 'md',
}: {
  icon?: ElementType
  active?: boolean
  size?: 'sm' | 'md'
}) {
  const { navigationIconColor } = useTheme()
  if (!Icon) return null

  return (
    <span
      className={[
        'flex shrink-0 items-center justify-center rounded-lg transition-colors duration-150',
        size === 'sm' ? 'size-7 [&>svg]:size-4' : 'size-8 [&>svg]:size-5',
        active ? 'text-white' : 'bg-transparent',
      ].join(' ')}
      style={
        active
          ? {
              backgroundColor: NAVIGATION_ICON_COLORS[navigationIconColor],
            }
          : {
              color: NAVIGATION_ICON_COLORS[navigationIconColor],
            }
      }
    >
      <Icon />
    </span>
  )
}

function SidebarMenuLink({ item, href }: { item: NavLink; href: string }) {
  const { setOpenMobile } = useSidebar()
  const isActive = checkIsActive(href, item)
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        asChild
        isActive={isActive}
        tooltip={item.title}
        className={[
          'relative h-10 gap-2.5 rounded-xl px-3 transition-colors duration-150 group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-0!',
          isActive
            ? 'bg-transparent text-[#0F172A] shadow-none hover:bg-transparent'
            : 'text-[#0F172A] hover:bg-[#F1F5F9] hover:text-[#0F172A]',
        ].join(' ')}
      >
        <Link to={item.url} onClick={() => setOpenMobile(false)}>
          <NavIcon icon={item.icon} active={isActive} />
          <span className='min-w-0 truncate text-sm font-medium text-[#0F172A] group-data-[collapsible=icon]:hidden'>
            {item.title}
          </span>
          {item.badge && <NavBadge>{item.badge}</NavBadge>}
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

function SidebarMenuCollapsible({
  item,
  href,
}: {
  item: NavCollapsible
  href: string
}) {
  const { setOpenMobile } = useSidebar()
  const isActive = checkIsActive(href, item, true)
  const [open, setOpen] = useState(false)
  const isOpen = isActive || open

  return (
    <Collapsible
      asChild
      open={isOpen}
      onOpenChange={setOpen}
      className='group/collapsible'
    >
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton
            tooltip={item.title}
            isActive={isActive}
            className={[
              'h-10 gap-2.5 rounded-xl px-3 transition-colors duration-150 group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-0!',
              isActive
                ? 'bg-transparent text-[#0F172A] hover:bg-transparent'
                : 'text-[#0F172A] hover:bg-[#F1F5F9] hover:text-[#0F172A]',
            ].join(' ')}
          >
            <NavIcon icon={item.icon} active={isActive} />
            <span className='min-w-0 truncate text-sm font-medium text-[#0F172A] group-data-[collapsible=icon]:hidden'>
              {item.title}
            </span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto size-4 text-muted-foreground/70 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90 rtl:rotate-180' />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent className='CollapsibleContent'>
          <SidebarMenuSub className='ms-5 mt-1 gap-1 border-sidebar-border/80 py-1 ps-3'>
            {item.items.map((subItem) => {
              const isSubActive = checkIsActive(href, subItem)
              return (
                <SidebarMenuSubItem key={subItem.title}>
                  <SidebarMenuSubButton
                    asChild
                    isActive={isSubActive}
                    className={[
                      'h-10 gap-2.5 rounded-xl px-3 transition-colors',
                      isSubActive
                        ? 'bg-transparent text-[#0F172A]'
                        : 'text-[#0F172A] hover:bg-[#F1F5F9] hover:text-[#0F172A]',
                    ].join(' ')}
                  >
                    <Link to={subItem.url} onClick={() => setOpenMobile(false)}>
                      <NavIcon icon={subItem.icon} active={isSubActive} />
                      <span className='min-w-0 truncate text-sm font-medium text-[#0F172A]'>
                        {subItem.title}
                      </span>
                      {subItem.badge && <NavBadge>{subItem.badge}</NavBadge>}
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              )
            })}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  )
}

function SidebarMenuCollapsedDropdown({
  item,
  href,
}: {
  item: NavCollapsible
  href: string
}) {
  const isActive = checkIsActive(href, item, true)

  return (
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <SidebarMenuButton
            tooltip={item.title}
            isActive={isActive}
            className={[
              'h-10 gap-2.5 rounded-xl px-3 transition-colors duration-150 group-data-[collapsible=icon]:mx-auto group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-0!',
              isActive
                ? 'bg-transparent text-[#0F172A] hover:bg-transparent'
                : 'text-[#0F172A] hover:bg-[#F1F5F9] hover:text-[#0F172A]',
            ].join(' ')}
          >
            <NavIcon icon={item.icon} active={isActive} />
            <span className='min-w-0 truncate text-sm font-medium text-[#0F172A]'>
              {item.title}
            </span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto size-4 text-muted-foreground/70 group-data-[collapsible=icon]:hidden' />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          side='right'
          align='start'
          sideOffset={8}
          className='min-w-52 rounded-xl p-1.5 shadow-lg'
        >
          <DropdownMenuLabel className='px-2 py-1.5 text-[10px] font-bold tracking-[0.14em] text-muted-foreground uppercase'>
            {item.title} {item.badge ? `(${item.badge})` : ''}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {item.items.map((sub) => {
            const isSubActive = checkIsActive(href, sub)

            return (
              <DropdownMenuItem
                key={`${sub.title}-${sub.url}`}
                asChild
                className={
                  isSubActive
                    ? 'rounded-lg bg-[#F1F5F9] text-[#0F172A]'
                    : 'rounded-lg text-[#0F172A]'
                }
              >
                <Link to={sub.url} className='gap-2.5'>
                  <NavIcon icon={sub.icon} active={isSubActive} />
                  <span className='max-w-52 truncate text-sm font-medium text-[#0F172A]'>
                    {sub.title}
                  </span>
                  {sub.badge && (
                    <span className='ms-auto text-xs'>{sub.badge}</span>
                  )}
                </Link>
              </DropdownMenuItem>
            )
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

function isPathActive(href: string, url?: string) {
  if (!url) return false

  const currentPath = href.split(/[?#]/)[0].replace(/\/+$/, '') || '/'
  const targetPath = url.split(/[?#]/)[0].replace(/\/+$/, '') || '/'

  return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`)
}

function checkIsActive(href: string, item: NavItem, mainNav = false) {
  const isItemActive = isPathActive(href, item.url)
  const isChildActive = !!item.items?.some((child) =>
    isPathActive(href, child.url)
  )

  return (
    isItemActive ||
    isChildActive ||
    (mainNav &&
      href.split('/')[1] !== '' &&
      href.split('/')[1] === item.url?.split('/')[1])
  )
}
