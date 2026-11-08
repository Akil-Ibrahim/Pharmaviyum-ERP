import {
  ArrowLeftRight,
  Bell,
  BookOpenCheck,
  Bot,
  Boxes,
  Building2,
  CalendarClock,
  ClipboardList,
  ClipboardCheck,
  Code2,
  FileText,
  LayoutDashboard,
  ListChecks,
  PackageCheck,
  Palette,
  ReceiptText,
  RefreshCw,
  ServerCog,
  Settings,
  ShoppingCart,
  Store,
  Truck,
  UserCog,
  UserRound,
  UsersRound,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'admin',
    email: 'admin@pharmaviyum.local',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [
    {
      name: 'Pharmaviyum',
      logo: '/images/pharmaviyum_logo.png',
      plan: 'Pharmacy workflow',
    },
  ],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: LayoutDashboard },
        { title: 'POS', url: '/pos', icon: ReceiptText },
        { title: 'Mortarium AI', url: '/mortarium-ai', icon: Bot },
        { title: 'Drug Reference', url: '/drug-reference', icon: BookOpenCheck },
        { title: 'Catalog Review', url: '/drug-catalog-review', icon: ClipboardCheck },
        { title: 'Patients', url: '/patients', icon: UserRound },
        { title: 'Orders', url: '/orders', icon: ClipboardList },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
        {
          title: 'Pharmacy',
          icon: Building2,
          items: [
            { title: 'Inventory', url: '/inventory', icon: Boxes },
            { title: 'Procurement', url: '/procurement', icon: ShoppingCart },
            { title: 'Transfers', url: '/transfers', icon: ArrowLeftRight },
            { title: 'Expiry Control', url: '/expiry-control', icon: CalendarClock },
            { title: 'Batches', url: '/batches', icon: PackageCheck },
            { title: 'Pharmacies', url: '/pharmacies', icon: Store },
            { title: 'Suppliers', url: '/suppliers', icon: Truck },
          ],
        },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users', url: '/users', icon: UsersRound },
        {
          title: 'Settings',
          icon: Settings,
          items: [
            { title: 'Profile', url: '/settings', icon: UserCog },
            { title: 'Account', url: '/settings/account', icon: UserRound },
            { title: 'Appearance', url: '/settings/appearance', icon: Palette },
            { title: 'Notifications', url: '/settings/notifications', icon: Bell },
            { title: 'Developer Tools', url: '/settings/developer', icon: Code2 },
          ],
        },
      ],
    },
    {
      title: 'Integrations',
      items: [
        { title: 'ERP Systems', url: '/erp-systems', icon: ServerCog },
        { title: 'Sync Events', url: '/sync-events', icon: RefreshCw },
        { title: 'Tasks', url: '/tasks', icon: ListChecks },
      ],
    },
  ],
}
