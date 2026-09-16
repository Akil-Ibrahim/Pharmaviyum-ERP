import {
  Bell,
  Boxes,
  ClipboardList,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Lock,
  MapPin,
  Package,
  Palette,
  Settings,
  ShieldCheck,
  Truck,
  UserCog,
  UserX,
  Users,
  Wrench,
  Zap,
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
      logo: ShieldCheck,
      plan: 'Pharmacy CRM',
    },
  ],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: LayoutDashboard },
        { title: 'Patients', url: '/patients', icon: Users },
        { title: 'Orders', url: '/orders', icon: ClipboardList },
        { title: 'Products', url: '/products', icon: Package },
        { title: 'Inventory', url: '/inventory', icon: Boxes },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
      ],
    },
    {
      title: 'Infrastructure',
      items: [
        { title: 'Pharmacies', url: '/pharmacies', icon: MapPin },
        { title: 'Suppliers', url: '/suppliers', icon: Truck },
        { title: 'ERP Sync', url: '/erp-sync', icon: Zap },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users', url: '/users', icon: Users },
        { title: 'Audit Logs', url: '/audit-logs', icon: Lock },
      ],
    },
    {
      title: 'Settings',
      items: [
        {
          title: 'Settings',
          icon: Settings,
          items: [
            { title: 'Profile', url: '/settings', icon: UserCog },
            { title: 'Account', url: '/settings/account', icon: Wrench },
            { title: 'Appearance', url: '/settings/appearance', icon: Palette },
            { title: 'Notifications', url: '/settings/notifications', icon: Bell },
          ],
        },
        { title: 'Help Center', url: '/help-center', icon: HelpCircle },
        { title: 'Forbidden', url: '/errors/forbidden', icon: UserX },
      ],
    },
  ],
}
