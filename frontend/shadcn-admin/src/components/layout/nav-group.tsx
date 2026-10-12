import { type ReactNode } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
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
      <SidebarGroupLabel
        className='px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/80'
      >
        {title}
      </SidebarGroupLabel>
      <SidebarMenu>
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
  return <Badge className='rounded-full px-1 py-0 text-xs'>{children}</Badge>
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
      >
        <Link to={item.url} onClick={() => setOpenMobile(false)}>
          {item.icon && (
            <span
              className={[
                'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 [&>svg]:size-[18px]',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-primary/10 text-primary group-hover:bg-primary/15',
              ].join(' ')}
            >
              <item.icon />
            </span>
          )}
          <span className='font-semibold text-black dark:text-white'>{item.title}</span>
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
  return (
    <Collapsible
      asChild
      defaultOpen={checkIsActive(href, item, true)}
      className='group/collapsible'
    >
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton tooltip={item.title} isActive={isActive}>
            {item.icon && (
              <span
                className={[
                  'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 [&>svg]:size-[18px]',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-primary/10 text-primary group-hover:bg-primary/15',
                ].join(' ')}
              >
                <item.icon />
              </span>
            )}
            <span className='font-semibold text-black dark:text-white'>{item.title}</span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto text-primary transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90 rtl:rotate-180' />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent className='CollapsibleContent'>
          <SidebarMenuSub>
            {item.items.map((subItem) => (
              <SidebarMenuSubItem key={subItem.title}>
                <SidebarMenuSubButton
                  asChild
                  isActive={checkIsActive(href, subItem)}
                >
                  <Link to={subItem.url} onClick={() => setOpenMobile(false)}>
                    {subItem.icon && (
                      <span
                        className={[
                          'flex size-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 [&>svg]:size-4',
                          checkIsActive(href, subItem)
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'bg-primary/10 text-primary group-hover:bg-primary/15',
                        ].join(' ')}
                      >
                        <subItem.icon />
                      </span>
                    )}
                    <span className='font-semibold text-black dark:text-white'>{subItem.title}</span>
                    {subItem.badge && <NavBadge>{subItem.badge}</NavBadge>}
                  </Link>
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            ))}
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
          <SidebarMenuButton tooltip={item.title} isActive={isActive}>
            {item.icon && (
              <span
                className={[
                  'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 [&>svg]:size-[18px]',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-primary/10 text-primary group-hover:bg-primary/15',
                ].join(' ')}
              >
                <item.icon />
              </span>
            )}
            <span className='font-semibold text-black dark:text-white'>
              {item.title}
            </span>
            {item.badge && <NavBadge>{item.badge}</NavBadge>}
            <ChevronRight className='ms-auto text-primary transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90' />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent side='right' align='start' sideOffset={4}>
          <DropdownMenuLabel>
            {item.title} {item.badge ? `(${item.badge})` : ''}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {item.items.map((sub) => {
            const isSubActive = checkIsActive(href, sub)

            return (
              <DropdownMenuItem key={`${sub.title}-${sub.url}`} asChild>
                <Link
                  to={sub.url}
                  className={isSubActive ? 'bg-secondary' : ''}
                >
                  {sub.icon && (
                    <span
                      className={[
                        'flex size-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 [&>svg]:size-4',
                        isSubActive
                          ? 'bg-primary text-primary-foreground shadow-sm'
                          : 'bg-primary/10 text-primary',
                      ].join(' ')}
                    >
                      <sub.icon />
                    </span>
                  )}
                  <span className='max-w-52 text-wrap font-semibold text-black dark:text-white'>
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
function checkIsActive(href: string, item: NavItem, mainNav = false) {
  return (
    href === item.url || // /endpint?search=param
    href.split('?')[0] === item.url || // endpoint
    !!item?.items?.filter((i) => i.url === href).length || // if child nav is active
    (mainNav &&
      href.split('/')[1] !== '' &&
      href.split('/')[1] === item?.url?.split('/')[1])
  )
}
