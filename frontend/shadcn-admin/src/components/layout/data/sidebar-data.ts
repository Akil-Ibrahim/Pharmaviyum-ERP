import {
  Bell,
  Bot,
  Boxes,
  ClipboardList,
  FileText,
  LayoutDashboard,
  MapPin,
  Package,
  Settings,
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
  teams: [
    {
      name: 'Pharmaviyum',
      logo: '/images/pharmaviyum_logo.png',
      plan: 'Pharmacy CRM',
    },
  ],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: LayoutDashboard },
        { title: 'POS', url: '/pos', icon: ClipboardList },
        { title: 'Patients', url: '/patients', icon: Users },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
      ],
    },
    {
      title: 'Pharmacy',
      items: [
        { title: 'Products', url: '/products', icon: Package },
        { title: 'Inventory', url: '/inventory', icon: Boxes },
        { title: 'Batches', url: '/batches', icon: Boxes },
        { title: 'Pharmacies', url: '/pharmacies', icon: MapPin },
        { title: 'Suppliers', url: '/suppliers', icon: Truck },
      ],
    },
    {
      title: 'Mortarium AI',
      items: [{ title: 'Mortarium AI', url: '/mortarium-ai', icon: Bot }],
    },
    {
      title: 'Integrations',
      items: [
        { title: 'ERP Systems', url: '/erp-systems', icon: Boxes },
        { title: 'Sync Events', url: '/sync-events', icon: ClipboardList },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users', url: '/users', icon: Users },
        { title: 'Tasks', url: '/tasks', icon: ClipboardList },
        {
          title: 'Settings',
          icon: Settings,
          items: [
            { title: 'Profile', url: '/settings', icon: UserCog },
            { title: 'Account', url: '/settings/account', icon: UserCog },
            { title: 'Appearance', url: '/settings/appearance', icon: Settings },
            { title: 'Notifications', url: '/settings/notifications', icon: Bell },
          ],
        },
      ],
    },
  ],
}
