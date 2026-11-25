import { type LinkProps } from '@tanstack/react-router'

type User = {
  name: string
  email: string
  avatar: string
}

type Team = {
  name: string
  logo: string
  plan: string
}

type BaseNavItem = {
  title: string
  badge?: string
  icon?: React.ElementType
  disabled?: boolean
  disabledReason?: string
}

type NavLink = BaseNavItem &
  (
    | {
        url: LinkProps['to'] | (string & {})
        items?: never
      }
    | {
        url?: never
        disabled: true
        items?: never
      }
  )

type NavCollapsible = BaseNavItem & {
  items: NavLink[]
  url?: never
}

type NavItem = NavCollapsible | NavLink

type NavGroup = {
  title: string
  items: NavItem[]
}

type SidebarData = {
  user: User
  teams: Team[]
  navGroups: NavGroup[]
}

export type { SidebarData, NavGroup, NavItem, NavCollapsible, NavLink }
