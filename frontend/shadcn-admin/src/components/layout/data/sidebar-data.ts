import {
  ArrowLeftRight,
  Bell,
  Bot,
  Boxes,
  CalendarClock,
  ClipboardList,
  FileText,
  LayoutDashboard,
  MapPin,
  Package,
  Settings,
  ShieldCheck,
  Truck,
  UserCog,
  Users,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Pharmaviyum Admin',
    email: 'admin@pharmaviyum.local',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [{ name: 'Pharmaviyum', logo: ShieldCheck, plan: 'Pharmacy ERP' }],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: LayoutDashboard },
        { title: 'POS', url: '/pos', icon: ClipboardList },
        { title: 'Patients', url: '/patients', icon: Users },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
        { title: 'Mortarium AI', url: '/mortarium-ai', icon: Bot },
        { title: 'Products', url: '/products', icon: Package },
        { title: 'Inventory', url: '/inventory', icon: Boxes },
        { title: 'Procurement', url: '/procurement', icon: Truck },
        { title: 'Transfers', url: '/transfers', icon: ArrowLeftRight },
        { title: 'Expiry Control', url: '/expiry-control', icon: CalendarClock },
      ],
    },
    {
      title: 'Pharmacy',
      items: [
        { title: 'Suppliers', url: '/suppliers', icon: Truck },
        { title: 'Pharmacies / Locations', url: '/pharmacies', icon: MapPin },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users / Staff', url: '/users', icon: Users },
        { title: 'Audit Logs', url: '/audit-logs', icon: ShieldCheck },
        {
          title: 'Settings',
          icon: Settings,
          items: [
            { title: 'Profile', url: '/settings', icon: UserCog },
            { title: 'Account', url: '/settings/account', icon: UserCog },
            { title: 'Appearance', url: '/settings/appearance', icon: Settings },
            { title: 'Notifications', url: '/settings/notifications', icon: Bell },
            { title: 'Developer Tools', url: '/settings/developer', icon: Settings },
          ],
        },
      ],
    },
  ],
}
