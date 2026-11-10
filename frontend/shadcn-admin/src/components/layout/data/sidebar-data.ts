import {
  ArrowLeftRight,
  Bell,
  BookOpenCheck,
  Bot,
  Boxes,
  CalendarClock,
  ClipboardCheck,
  ClipboardList,
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
        { title: 'Patients', url: '/patients', icon: UserRound },
        { title: 'Prescriptions', url: '/prescriptions', icon: FileText },
        {
          title: 'Inventory',
          icon: Boxes,
          items: [
            {
              title: 'Drug Catalog',
              url: '/drug-reference',
              icon: BookOpenCheck,
            },
            {
              title: 'Catalog Review',
              url: '/drug-catalog-review',
              icon: ClipboardCheck,
            },
            { title: 'Stock Overview', url: '/inventory', icon: Boxes },
            { title: 'Batches', url: '/batches', icon: PackageCheck },
            {
              title: 'Expiry Management',
              url: '/expiry-control',
              icon: CalendarClock,
            },
            { title: 'Transfers', url: '/transfers', icon: ArrowLeftRight },
          ],
        },
        {
          title: 'Procurement',
          icon: ShoppingCart,
          items: [
            { title: 'Suppliers', url: '/suppliers', icon: Truck },
            { title: 'Purchase Orders', url: '/orders', icon: ClipboardList },
            { title: 'Receiving', url: '/procurement', icon: PackageCheck },
          ],
        },
        { title: 'Pharmacies', url: '/pharmacies', icon: Store },
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
            { title: 'Appearance', url: '/settings/appearance', icon: Palette },
            {
              title: 'Notifications',
              url: '/settings/notifications',
              icon: Bell,
            },
            {
              title: 'Developer Tools',
              url: '/settings/developer',
              icon: Code2,
            },
          ],
        },
      ],
    },
    {
      title: 'System',
      items: [
        {
          title: 'Integrations',
          icon: ServerCog,
          items: [
            { title: 'ERP Connections', url: '/erp-systems', icon: ServerCog },
            { title: 'Sync History', url: '/sync-events', icon: RefreshCw },
          ],
        },
        { title: 'Background Tasks', url: '/tasks', icon: ListChecks },
      ],
    },
  ],
}
