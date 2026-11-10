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
    <SidebarGroup className='px-2 py-1.5'>
      <SidebarGroupLabel className='h-7 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground/75'>
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
    <Badge className='ms-auto rounded-md border border-primary/15 bg-primary/10 px-1.5 py-0 text-[10px] font-bold text-primary shadow-none'>
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
  const iconColor = NAVIGATION_ICON_COLORS[navigationIconColor]

  if (!Icon) return null

  return (
    <span
      className={[
        'flex shrink-0 items-center justify-center rounded-lg transition-colors duration-150',
        size === 'sm' ? 'size-7 [&>svg]:size-4' : 'size-8 [&>svg]:size-[18px]',
        active
          ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
          : 'bg-transparent group-hover/menu-button:bg-primary/10',
      ].join(' ')}
      style={{ color: iconColor }}
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
          'relative h-10 gap-2.5 rounded-xl px-2.5 transition-all duration-150',
          isActive
            ? 'bg-primary/10 text-foreground shadow-none hover:bg-primary/15 before:absolute before:inset-y-2 before:start-0 before:w-[3px] before:rounded-full before:bg-primary'
            : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
        ].join(' ')}
      >
        <Link to={item.url} onClick={() => setOpenMobile(false)}>
          <NavIcon icon={item.icon} active={isActive} />
          <span className='min-w-0 truncate text-[13px] font-semibold text-foreground'>
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
              'h-10 gap-2.5 rounded-xl px-2.5 transition-all duration-150',
              isActive
                ? 'bg-primary/10 text-foreground hover:bg-primary/15'
                : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
            ].join(' ')}
          >
            <NavIcon icon={item.icon} active={isActive} />
            <span className='min-w-0 truncate text-[13px] font-semibold text-foreground'>
              {item.title}
            </span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto size-4 text-muted-foreground/70 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90 rtl:rotate-180' />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent className='CollapsibleContent'>
          <SidebarMenuSub className='ms-5 mt-1 gap-1 border-sidebar-border/80 ps-3 py-1'>
            {item.items.map((subItem) => {
              const isSubActive = checkIsActive(href, subItem)
              return (
                <SidebarMenuSubItem key={subItem.title}>
                  <SidebarMenuSubButton
                    asChild
                    isActive={isSubActive}
                    className={[
                      'h-10 gap-2.5 rounded-xl px-2.5 transition-colors',
                      isSubActive
                        ? 'bg-primary/10 font-semibold text-foreground'
                        : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
                    ].join(' ')}
                  >
                    <Link to={subItem.url} onClick={() => setOpenMobile(false)}>
                      <NavIcon icon={subItem.icon} active={isSubActive} />
                      <span className='min-w-0 truncate text-[13px] font-semibold text-foreground'>
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
              'h-10 gap-2.5 rounded-xl px-2.5 transition-all duration-150',
              isActive
                ? 'bg-primary/10 text-foreground hover:bg-primary/15'
                : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
            ].join(' ')}
          >
            <NavIcon icon={item.icon} active={isActive} />
            <span className='min-w-0 truncate text-[13px] font-semibold text-foreground'>
              {item.title}
            </span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto size-4 text-muted-foreground/70' />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          side='right'
          align='start'
          sideOffset={8}
          className='min-w-52 rounded-xl p-1.5 shadow-lg'
        >
          <DropdownMenuLabel className='px-2 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-muted-foreground'>
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
                    ? 'rounded-lg bg-primary/10 text-foreground'
                    : 'rounded-lg'
                }
              >
                <Link to={sub.url} className='gap-2.5'>
                  <NavIcon icon={sub.icon} active={isSubActive} />
                  <span className='max-w-52 truncate text-[13px] font-semibold text-foreground'>
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
