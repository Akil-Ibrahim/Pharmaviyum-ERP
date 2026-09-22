import {
  Bell,
  Bot,
  Boxes,\n  ClipboardCheck,\n  DatabaseZap,\n  HeartPulse,\n  House,\n  PackageSearch,\n  ReceiptText,\n  Sparkles,\n  Stethoscope,\n  Warehouse,
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
  teams: [{ name: 'Pharmaviyum', logo: ShieldCheck, plan: 'Pharmacy CRM' }],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: House },
        { title: 'Patients', url: '/patients', icon: HeartPulse },
        { title: 'Orders', url: '/orders', icon: ClipboardCheck },
        { title: 'Prescriptions', url: '/prescriptions', icon: ReceiptText },
      ],
    },
    {
      title: 'Pharmacy',
      items: [
        { title: 'Products', url: '/products', icon: PackageSearch },
        { title: 'Inventory', url: '/inventory', icon: Warehouse },
        { title: 'Batches', url: '/batches', icon: Boxes },
        { title: 'Pharmacies', url: '/pharmacies', icon: Stethoscope },
        { title: 'Suppliers', url: '/suppliers', icon: DatabaseZap },
      ],
    },
    {
      title: 'Mortarium AI',
      items: [{ title: 'Mortarium AI', url: '/mortarium-ai', icon: Sparkles }],
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
