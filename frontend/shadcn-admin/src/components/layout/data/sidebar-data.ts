import {
  ArrowLeftRight,
  Bell,
  BookOpenCheck,
  Bot,
  Boxes,
  CalendarClock,
  ClipboardList,
  Code2,
  FileText,
  LayoutDashboard,
  ListChecks,
  PackageCheck,
  Palette,
  Pill,
  ReceiptText,
  RefreshCw,
  ServerCog,
  Settings,
  ShoppingCart,
  Store,
  Stethoscope,
  Truck,
  UserCog,
  UserRound,
  UsersRound,
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
      plan: 'Pharmacy workflow',
    },
  ],
  navGroups: [
    {
      title: 'Operations',
      items: [
        { title: 'Dashboard', url: '/', icon: LayoutDashboard },
        { title: 'Pharmacist Workspace', url: '/pharmacist-workspace', icon: Stethoscope },
        { title: 'POS', url: '/pos', icon: ReceiptText },
        { title: 'Drug Reference', url: '/drug-reference', icon: BookOpenCheck },
        { title: 'Patients', url: '/patients', icon: UserRound },
        { title: 'Products', url: '/products', icon: Pill },
        { title: 'Orders', url: '/orders', icon: ClipboardList },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
      ],
    },
    {
      title: 'Pharmacy',
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
    {
      title: 'Mortarium AI',
      items: [{ title: 'Mortarium AI', url: '/mortarium-ai', icon: Bot }],
    },
    {
      title: 'Integrations',
      items: [
        { title: 'ERP Systems', url: '/erp-systems', icon: ServerCog },
        { title: 'Sync Events', url: '/sync-events', icon: RefreshCw },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users', url: '/users', icon: UsersRound },
        { title: 'Tasks', url: '/tasks', icon: ListChecks },
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
  ],
}
